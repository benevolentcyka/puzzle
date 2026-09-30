"""Cross the explicit 'I STNM' interpretation with independent section layouts.

The earlier nearby-I tests used GLOBAL formatting policies. This checks the
same human-readable signature interpretations on the new independently
formatted section buffers. It has no MD5 prefix filter and checks both escrows.
"""
import argparse
import bisect
import datetime
import functools
import hashlib
import importlib.util
import json
import random
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
spec=importlib.util.spec_from_file_location('signature_section_support',HERE/'chapter-sections.py')
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
ORIGINAL=list(S.PARAS)
STYLES={
    'first':[3,91,164,233],
    'nearest':[3,91,166,233],
    'all':[3,91,164,165,166,233],
}
I_POSITIONS=[3,91,164,165,166,233]
KNOWN_STYLES=['first','nearest','all']
for selection in range(1,1<<len(I_POSITIONS)):
    positions=[p for bit,p in enumerate(I_POSITIONS) if selection>>bit&1]
    if positions not in STYLES.values():
        STYLES[f'subset-{selection:02d}']=positions
assert len(STYLES)==63 and len({tuple(p) for p in STYLES.values()})==63


def activate(style):
    """Only explicit paragraph-initial I bytes are altered; keep original text."""
    S.PARAS=list(ORIGINAL)
    S.cased.cache_clear()
    for p in STYLES[style]:
        assert S.PARAS[p].startswith('I ')
        S.PARAS[p]='i'+S.PARAS[p][1:]


def build(styles,masks,voices):
    bases=[dict(style=style,mask=m,start=start,join=join,tail_hex=tail.hex())
           for style in styles for m in masks for start in [0,1,3]
           for join in ['lf','crlf'] for tail in [b'',b'\n',b'\r\n']]
    cumulative=[0]
    manifest=[]
    stream=hashlib.sha256()
    rng=random.Random(777)
    checks=0
    last=time.monotonic()
    for number,label in enumerate(bases):
        activate(label['style'])
        b=S.Base(label,voices)
        manifest.append(dict(base=label,sections=b.counts,texts=b.count))
        for section in b.sections:
            for value,policy in section:
                stream.update(len(value).to_bytes(4,'big'))
                stream.update(value)
                stream.update(json.dumps(policy,sort_keys=True).encode())
        for rank in sorted({0,b.count-1,rng.randrange(b.count)}):
            exact=S.reference(b.describe(rank))
            assert b.witness(rank)==exact and b.digest(rank)==hashlib.md5(exact).digest()
            checks+=1
        cumulative.append(cumulative[-1]+b.count)
        now=time.monotonic()
        if now-last>=20:
            print(f'Validating layout plan: {number+1:,}/{len(bases):,} bases',flush=True)
            last=now
    return bases,cumulative,manifest,stream.hexdigest(),checks


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--i-styles',default='first,nearest,all',
                    help='Comma-separated styles, exhaustive (all 63 subsets), or remaining (60 other subsets)')
    ap.add_argument('--group-masks',default=','.join(map(str,S.MASKS)))
    ap.add_argument('--voice',choices=['both','keep'],default='both')
    ap.add_argument('--indices',default='0,1,2,3,4,5,6')
    ap.add_argument('--platform',type=int,default=1)
    ap.add_argument('--batch',type=int,default=16384)
    ap.add_argument('--limit',type=int,help='Additional entropy candidates, then checkpoint and stop')
    ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args()
    if sys.flags.optimize:
        ap.error('Python -O disables required verification')
    styles=(list(STYLES) if args.i_styles=='exhaustive' else
            [s for s in STYLES if s not in KNOWN_STYLES] if args.i_styles=='remaining' else args.i_styles.split(','))
    masks=[int(x) for x in args.group_masks.split(',')]
    indices=[int(x) for x in args.indices.split(',')]
    if not styles or len(set(styles))!=len(styles) or any(s not in STYLES for s in styles):
        ap.error('Use distinct first, nearest, all styles')
    if not masks or len(set(masks))!=len(masks) or any(m<0 or m>15 for m in masks):
        ap.error('Use distinct group masks from 0 to 15')
    if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices):
        ap.error('Use distinct nonhardened address indices')
    if args.batch<1 or (args.limit is not None and args.limit<1):
        ap.error('Positive batch/limit required')
    bases,cumulative,manifest,stream,checks=build(styles,masks,args.voice=='both')
    total=cumulative[-1]
    print(f'PASS: {checks} serialization checks; {total:,} candidates x {len(indices)} indices',flush=True)
    if args.verify_only:
        return
    wallet=S.J.Wallet(args.platform,indices)
    from checkpoint_io import atomic_json
    from bip_utils import Bip32Secp256k1
    from bip39_gpu.gpu.bip32_gpu import hash160_to_p2pkh,base58check_encode
    np=wallet.np
    files=[Path(__file__),HERE/'chapter-sections.py',ROOT/'wattpad-paragraphs.json',
           ROOT/'joint-format-2026-09-28/search.py',ROOT/'joint-format-2026-09-28/checkpoint_io.py',
           ROOT/'assumptions-2026-09-27/search-assumptions.py',ROOT/'followup-2026-09-26/language-settings-gpu.py',
           ROOT/'gpu-case-pairs.py',ROOT/'expanded-2026-09-26/wallet_paths_gpu.py']
    config=dict(family='i-stnm-independent-section-layouts-v1',styles={k:STYLES[k] for k in styles},
                masks=masks,voice=args.voice,indices=indices,targets=S.TARGETS,parent=S.PARENT,
                entropy='raw-md5',language='english',passphrase='',prefix_filter=None,
                regions=S.REGIONS,base_count=len(manifest),
                manifest_sha256=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
                section_stream_sha256=stream,
                crypto_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),wallet_kernel_sha256=wallet.gpu.kernel_sha256,
                source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    dest=HERE/f'chapter-signatures-{tag}.json'
    plan=HERE/f'chapter-signatures-plan-{tag}.json'
    if not plan.exists():
        atomic_json(plan,dict(configuration=config,bases=manifest,candidates_total=total))
    elif json.loads(plan.read_bytes())!=dict(configuration=config,bases=manifest,candidates_total=total):
        raise RuntimeError('Saved search plan differs')
    @functools.lru_cache(maxsize=2)
    def cached_base(i):
        activate(bases[i]['style'])
        return S.Base(bases[i],args.voice=='both')
    def locate(rank):
        i=bisect.bisect_right(cumulative,rank)-1
        b=cached_base(i)
        # A cached Base can belong to a different style from the current globals.
        # Restore that style before the independent reference builds its buffer.
        if S.PARAS!=originals_by_style[b.label['style']]:
            activate(b.label['style'])
        return b,rank-cumulative[i]
    originals_by_style={}
    for style in styles:
        activate(style)
        originals_by_style[style]=list(S.PARAS)
    with S.J.exclusive(dest.with_suffix('.lock')):
        state=json.loads(dest.read_bytes()) if dest.exists() else dict(configuration=config,next_rank=0,
            candidates_total=total,derived_addresses=0,matches=[],complete=False,elapsed_seconds=0.0,
            serializer_checks=checks,sampled_cpu_comparisons=0)
        if state['configuration']!=config or state['candidates_total']!=total:
            raise RuntimeError('Checkpoint identity mismatch')
        if state['complete'] or state['matches']:
            print(f'Already finished: {dest.name}',flush=True)
            return
        stop=min(total,state['next_rank']+args.limit) if args.limit else total
        elapsed=state['elapsed_seconds']
        previous_comparisons=state['sampled_cpu_comparisons']
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
                exact=S.reference(b.describe(p))
                assert b.witness(p)==exact and hashlib.md5(exact).digest()==entropy[k]
            words,seeds,out=wallet.derive(entropy,indices)
            wallet.compare(words,seeds,out,[(k,entropy[k]) for k in sample],indices)
            for wanted,address in wallet.targets.items():
                for row in np.flatnonzero(np.all(out[0]==np.frombuffer(wanted,dtype=np.uint8),axis=1)):
                    k,j=divmod(int(row),len(indices))
                    b,p=locate(start+k)
                    exact=S.reference(b.describe(p))
                    assert hashlib.md5(exact).digest()==entropy[k]
                    seed=hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
                    path=f'{S.PARENT}/{indices[j]}'
                    node=Bip32Secp256k1.FromSeed(seed).DerivePath(path)
                    pub=node.PublicKey().RawCompressed().ToBytes()
                    assert hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())==address
                    found=HERE/f'FOUND-chapter-signatures-{tag}.txt'
                    found.write_bytes(exact)
                    atomic_json(found.with_suffix('.json'),dict(address=address,path=path,md5=entropy[k].hex(),
                        mnemonic=words[k],private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),
                        metadata=b.describe(p),configuration=config))
                    state['matches'].append(dict(address=address,file=found.name))
            state['next_rank']+=size
            state['derived_addresses']+=size*len(indices)
            state['complete']=state['next_rank']==total
            state['serializer_checks']+=len(sample)
            state['sampled_cpu_comparisons']=previous_comparisons+wallet.comparisons
            state['elapsed_seconds']=elapsed+time.monotonic()-begin
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
