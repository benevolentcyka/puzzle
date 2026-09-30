"""Independent clipboard policies for the three sections of the final chapter.

All ten embedded line breaks, six NBSPs, and paragraph/pre-break trailing
spaces are handled by independently chosen SECTION policies. This crosses
artifact classes and can alter many sites together. Paragraph joins remain
uniformly two LF or two CRLF, following the revised public clue. No hint filter.
"""
from __future__ import annotations

import argparse
import bisect
import datetime
import functools
import hashlib
import importlib.util
import itertools
import json
import random
import re
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'joint-format-2026-09-28'))
from checkpoint_io import atomic_json
spec=importlib.util.spec_from_file_location('section_wallet_support',ROOT/'joint-format-2026-09-28/search.py')
J=importlib.util.module_from_spec(spec)
spec.loader.exec_module(J)
PARAS=json.loads((ROOT/'wattpad-paragraphs.json').read_bytes())
GROUPS=[[4,5,6,7],[92,93,94,95],[167,168,169,170],[230,231,232,234]]
REGIONS=[[0,87],[87,162],[162,273]]
TARGETS=['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W','1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']
PARENT="m/44'/0'/0'/0"
MASKS=[15,7,0]+[i for i in range(16) if i not in (15,7,0)]


def upper_lower(text):
    chars=list(text)
    letters=[i for i,c in enumerate(text) if c.isascii() and c.isalpha()]
    chars[letters[0]]=chars[letters[0]].lower()
    chars[letters[-1]]=chars[letters[-1]].upper()
    return ''.join(chars)


@functools.lru_cache(maxsize=16)
def cased(mask):
    selected={p for bit,g in enumerate(GROUPS) if mask>>bit&1 for p in g}
    return [upper_lower(p) if i in selected else p for i,p in enumerate(PARAS)]


def choices(section, join, voices):
    return [dict(internal=internal,tails=tails,nbsp=nbsp,voice=voice)
            for internal in ['keep','platform','promote','space','delete']
            for tails in ['keep','trim']
            for nbsp in (['keep'] if section==0 else ['space','keep','delete'])
            for voice in (['keep','vOIce'] if section==0 and voices else ['keep'])]


def transform(text, policy, join, paragraph):
    if policy['voice']=='vOIce' and paragraph==11:
        assert text=='A pleasant female voice.'
        text=text.replace('voice','vOIce')
    if policy['nbsp']!='keep':
        text=text.replace('\u00a0',' ' if policy['nbsp']=='space' else '')
    if policy['tails']=='trim':
        # Trims only paragraph/pre-embedded-break spaces, leaving word spacing.
        text=re.sub(r' +(?=\n|$)','',text)
    ending='\n' if join=='lf' else '\r\n'
    new={'keep':'\n','platform':ending,'promote':ending*2,'space':' ','delete':''}[policy['internal']]
    return text.replace('\n',new).encode('utf8')


class Base:
    def __init__(self,label,voices):
        self.label=label
        self.sep=b'\n\n' if label['join']=='lf' else b'\r\n\r\n'
        self.sections=[]
        for section,(start,stop) in enumerate(REGIONS):
            start=max(start,label['start'])
            unique={}
            for policy in choices(section,label['join'],voices):
                value=self.sep.join(transform(cased(label['mask'])[i],policy,label['join'],i)
                                    for i in range(start,stop))
                unique.setdefault(value,policy)
            self.sections.append([(value,policy) for value,policy in unique.items()])
        self.counts=[len(s) for s in self.sections]
        self.count=self.counts[0]*self.counts[1]*self.counts[2]
        self.prefixes={}

    def locate(self,rank):
        a,r=divmod(rank,self.counts[1]*self.counts[2])
        b,c=divmod(r,self.counts[2])
        return a,b,c

    def digest(self,rank):
        a,b,c=self.locate(rank)
        if (a,b) not in self.prefixes:
            md=hashlib.md5(self.sections[0][a][0]+self.sep+self.sections[1][b][0]+self.sep)
            self.prefixes[a,b]=md
        md=self.prefixes[a,b].copy()
        md.update(self.sections[2][c][0])
        md.update(bytes.fromhex(self.label['tail_hex']))
        return md.digest()

    def witness(self,rank):
        ids=self.locate(rank)
        return self.sep.join(self.sections[i][j][0] for i,j in enumerate(ids))+bytes.fromhex(self.label['tail_hex'])

    def describe(self,rank):
        return dict(base=self.label,section_policies=[self.sections[i][j][1] for i,j in enumerate(self.locate(rank))])


def reference(metadata):
    """Independent full chapter walk, distinct from per-section cached MD5."""
    base=metadata['base']
    selected={p for bit,g in enumerate(GROUPS) if base['mask']>>bit&1 for p in g}
    policies=metadata['section_policies']
    paragraphs=[]
    separator='\n\n' if base['join']=='lf' else '\r\n\r\n'
    for i in range(base['start'],len(PARAS)):
        original=PARAS[i]
        policy=policies[0 if i<87 else 1 if i<162 else 2]
        if i in selected:
            raw=bytearray(original.encode())
            letters=[j for j,c in enumerate(raw) if 65<=c<=90 or 97<=c<=122]
            raw[letters[0]]|=32
            raw[letters[-1]]&=~32
            original=raw.decode()
        if i==11 and policy['voice']=='vOIce':
            original=original.replace('voice','vOIce')
        if policy['nbsp']=='space':
            original=original.replace('\u00a0',' ')
        elif policy['nbsp']=='delete':
            original=original.replace('\u00a0','')
        lines=original.split('\n')
        if policy['tails']=='trim':
            lines=[line.rstrip(' ') for line in lines]
        inside={'keep':'\n','platform':separator[:len(separator)//2],
                'promote':separator,'space':' ','delete':''}[policy['internal']]
        paragraphs.append(inside.join(lines))
    return separator.join(paragraphs).encode()+bytes.fromhex(base['tail_hex'])


def build(masks,voices):
    bases=[dict(mask=m,start=s,join=j,tail_hex=t.hex()) for m in masks for s in [0,1,3]
           for j in ['lf','crlf'] for t in [b'',b'\n',b'\r\n']]
    cumulative=[0]
    manifest=[]
    stream=hashlib.sha256()
    rng=random.Random(777)
    checks=0
    for label in bases:
        b=Base(label,voices)
        manifest.append(dict(base=label,sections=b.counts,texts=b.count))
        for section in b.sections:
            for text,policy in section:
                stream.update(len(text).to_bytes(4,'big'))
                stream.update(text)
                stream.update(json.dumps(policy,sort_keys=True).encode())
        for rank in sorted({0,b.count-1,rng.randrange(b.count)}):
            exact=reference(b.describe(rank))
            assert b.witness(rank)==exact
            assert b.digest(rank)==hashlib.md5(exact).digest()
            checks+=1
        cumulative.append(cumulative[-1]+b.count)
    # Byte-for-byte agreement with the already audited all-four draft baseline.
    policy=dict(internal='keep',tails='keep',nbsp='space',voice='keep')
    known=reference(dict(base=dict(mask=15,start=0,join='lf',tail_hex=''),section_policies=[policy]*3))
    assert known==(ROOT/'bases/four-groups-lflf-nbsp-space.txt').read_bytes()
    return bases,cumulative,manifest,stream.hexdigest(),checks+1


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--group-masks',default=','.join(map(str,MASKS)))
    ap.add_argument('--voice',choices=['both','keep'],default='both')
    ap.add_argument('--indices',default='0,1,2,3,4,5,6')
    ap.add_argument('--platform',type=int,default=1)
    ap.add_argument('--batch',type=int,default=16384)
    ap.add_argument('--limit',type=int,help='Maximum additional entropy candidates, then checkpoint and stop')
    ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args()
    if sys.flags.optimize:
        ap.error('Python -O disables required verification')
    masks=[int(x) for x in args.group_masks.split(',')]
    indices=[int(x) for x in args.indices.split(',')]
    if not masks or len(set(masks))!=len(masks) or any(i<0 or i>15 for i in masks):
        ap.error('Use distinct masks from 0 to 15')
    if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices):
        ap.error('Use distinct nonhardened address indices')
    if args.batch<1 or (args.limit is not None and args.limit<1):
        ap.error('Batch/limit must be positive')
    bases,cumulative,manifest,stream,checks=build(masks,args.voice=='both')
    total=cumulative[-1]
    print(f'PASS: {checks} serialization checks; {total:,} candidates x {len(indices)} indices',flush=True)
    if args.verify_only:
        return
    wallet=J.Wallet(args.platform,indices)
    from bip_utils import Bip32Secp256k1
    from bip39_gpu.gpu.bip32_gpu import hash160_to_p2pkh,base58check_encode
    np=wallet.np
    config=dict(family='independent-section-clipboard-policies-v1',masks=masks,voice=args.voice,indices=indices,
        targets=TARGETS,parent=PARENT,entropy='raw-md5',language='english',passphrase='',prefix_filter=None,
        regions=REGIONS,manifest=manifest,section_stream_sha256=stream,
        crypto_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),wallet_kernel_sha256=wallet.gpu.kernel_sha256,
        source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [
            Path(__file__),ROOT/'wattpad-paragraphs.json',ROOT/'joint-format-2026-09-28/search.py',
            ROOT/'joint-format-2026-09-28/checkpoint_io.py',ROOT/'assumptions-2026-09-27/search-assumptions.py',
            ROOT/'followup-2026-09-26/language-settings-gpu.py',ROOT/'gpu-case-pairs.py',
            ROOT/'expanded-2026-09-26/wallet_paths_gpu.py']})
    tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    dest=HERE/f'chapter-sections-{tag}.json'
    @functools.lru_cache(maxsize=2)
    def cached_base(i):
        return Base(bases[i],args.voice=='both')
    def locate(rank):
        i=bisect.bisect_right(cumulative,rank)-1
        return cached_base(i),rank-cumulative[i]
    with J.exclusive(dest.with_suffix('.lock')):
        state=json.loads(dest.read_bytes()) if dest.exists() else dict(configuration=config,next_rank=0,
            candidates_total=total,derived_addresses=0,matches=[],complete=False,elapsed_seconds=0.0,
            serializer_checks=checks,sampled_cpu_comparisons=0)
        if state['configuration']!=config or state['candidates_total']!=total:
            raise RuntimeError('Checkpoint identity mismatch')
        if state['complete'] or state['matches']:
            print(f'Already finished: {dest.name}',flush=True)
            return
        stop=min(total,state['next_rank']+args.limit) if args.limit else total
        initial_elapsed=state['elapsed_seconds']
        initial_comparisons=state['sampled_cpu_comparisons']
        begin=last=time.monotonic()
        print(f'{dest.name}: resume {state["next_rank"]:,}/{total:,}; no hash-prefix filter',flush=True)
        while state['next_rank']<stop:
            start=state['next_rank']
            size=min(args.batch,stop-start)
            entropy=[]
            for rank in range(start,start+size):
                b,p=locate(rank)
                entropy.append(b.digest(p))
            sample=sorted({0,size//2,size-1})
            for k in sample:
                b,p=locate(start+k)
                exact=reference(b.describe(p))
                assert b.witness(p)==exact and hashlib.md5(exact).digest()==entropy[k]
            words,seeds,out=wallet.derive(entropy,indices)
            wallet.compare(words,seeds,out,[(k,entropy[k]) for k in sample],indices)
            for wanted,address in wallet.targets.items():
                for r in np.flatnonzero(np.all(out[0]==np.frombuffer(wanted,dtype=np.uint8),axis=1)):
                    k,j=divmod(int(r),len(indices))
                    b,p=locate(start+k)
                    exact=reference(b.describe(p))
                    assert hashlib.md5(exact).digest()==entropy[k]
                    seed=hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
                    path=f'{PARENT}/{indices[j]}'
                    node=Bip32Secp256k1.FromSeed(seed).DerivePath(path)
                    pub=node.PublicKey().RawCompressed().ToBytes()
                    assert hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())==address
                    found=HERE/f'FOUND-chapter-sections-{tag}.txt'
                    found.write_bytes(exact)
                    atomic_json(found.with_suffix('.json'),dict(address=address,path=path,md5=entropy[k].hex(),
                        mnemonic=words[k],private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),
                        metadata=b.describe(p),configuration=config))
                    state['matches'].append(dict(address=address,file=found.name))
            state['next_rank']+=size
            state['derived_addresses']+=size*len(indices)
            state['complete']=state['next_rank']==total
            state['serializer_checks']+=len(sample)
            state['sampled_cpu_comparisons']=initial_comparisons+wallet.comparisons
            state['elapsed_seconds']=initial_elapsed+time.monotonic()-begin
            state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
            atomic_json(dest,state)
            now=time.monotonic()
            if now-last>=20 or state['next_rank']==stop or state['matches']:
                print(json.dumps({k:state[k] for k in ['next_rank','candidates_total','derived_addresses',
                    'complete','elapsed_seconds','matches']}),flush=True)
                last=now
            if state['matches']:
                print(f'CPU VERIFIED MATCH saved privately: {found}',flush=True)
                return


if __name__=='__main__':
    main()
