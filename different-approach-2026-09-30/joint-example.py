"""Joint capitalization and clipboard-layout hypotheses for the solved example.

The original question is verified against Aoi's seven published MD5 digits.
Every selected layout is crossed with all 21 paragraph/named letter choices,
or all 11 paired paragraph/named choices. A declared 3c6 filter is optional.
No signing, spending, broadcasting, network access, or arbitrary wallet targets.
"""
from __future__ import annotations

import argparse
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT/'joint-format-2026-09-28'))
sys.path.insert(0, str(ROOT/'expanded-2026-09-26'))
from checkpoint_io import atomic_json


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


J = module('joint_example_wallet_support', ROOT/'joint-format-2026-09-28/search.py')
Q = module('joint_example_filter_support', ROOT/'assumptions-2026-09-27/quoted-mask-search.py')
TARGET = '1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'
PARENT = "m/44'/0'/0'/0"
POSTS = json.loads((ROOT/'aoi-posts-archive.json').read_bytes())
QUESTION = next(p for p in POSTS if p['id']=='cleczc')['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0].encode('ascii')
assert hashlib.md5(QUESTION).hexdigest() == '7759227d7406d8230d7e3a8f7b9846d7'
PARAS = QUESTION.split(b'\n\n')
assert len(PARAS) == 10
# One/two anomalous joins, including a space on a blank line. The base retains
# two LF or two CRLF everywhere else. No global trim silently changes a buffer.
JOINS = [b'\n\n', b'\r\n\r\n', b'\n', b'\r\n', b'\n\n\n', b'\r\n\r\n\r\n', b'\n \n', b'\r\n \r\n']
SPACES = [b' ', b'  ', b'', b'\t', b'\xc2\xa0', b'\n', b'\r\n']


def layouts(family, defects):
    """Descriptors retain the original ten logical paragraphs for case roles."""
    output = []
    for base_join in [b'\n\n', b'\r\n\r\n']:
        if family == 'boundaries':
            alternatives = [x for x in JOINS if x != base_join]
            for degree in range(1, defects+1):
                for sites in itertools.combinations(range(9), degree):
                    for replacements in itertools.product(alternatives, repeat=degree):
                        output.append(dict(base_join_hex=base_join.hex(), changes=[
                            dict(kind='join', site=i, replacement_hex=v.hex()) for i,v in zip(sites,replacements)]))
        else:
            for p, text in enumerate(PARAS):
                for match in re.finditer(b' ', text):
                    for value in SPACES[1:]:
                        output.append(dict(base_join_hex=base_join.hex(), changes=[
                            dict(kind='space', paragraph=p, site=match.start(), replacement_hex=value.hex())]))
    return output


def reference(layout, mask=0, case_mode='independent'):
    """Independent paragraph walk: apply original case roles before joining."""
    paras = []
    bit = 0
    for p, original in enumerate(PARAS):
        text = bytearray(original)
        letters = [i for i,c in enumerate(original) if 65 <= c <= 90 or 97 <= c <= 122]
        if case_mode == 'independent':
            for pos in [letters[0], letters[-1]]:
                if mask & 1 << bit:
                    text[pos] ^= 32
                bit += 1
        else:
            if mask & 1 << bit:
                text[letters[0]] ^= 32
                text[letters[-1]] ^= 32
            bit += 1
        if b'post outing himself.' in original:
            pos = original.index(b'post outing himself.') + len(b'post outing himself') - 1
            if mask & 1 << bit:
                text[pos] ^= 32
            bit += 1
        changes = [x for x in layout['changes'] if x['kind']=='space' and x['paragraph']==p]
        for change in sorted(changes, key=lambda x:x['site'], reverse=True):
            pos=change['site']
            assert text[pos]==32
            text[pos:pos+1] = bytes.fromhex(change['replacement_hex'])
        paras.append(bytes(text))
    joins = [bytes.fromhex(layout['base_join_hex'])]*9
    for change in layout['changes']:
        if change['kind']=='join':
            joins[change['site']] = bytes.fromhex(change['replacement_hex'])
    output = paras[0]
    for join, paragraph in zip(joins, paras[1:]):
        output += join + paragraph
    return output


def prepared(layout, case_mode):
    """Map original role bytes into the independently serialized buffer."""
    source=reference(layout)
    groups=[]
    offset=0
    for p, original in enumerate(PARAS):
        letter=[i for i,c in enumerate(original) if 65<=c<=90 or 97<=c<=122]
        local = [[letter[0]],[letter[-1]]] if case_mode=='independent' else [[letter[0],letter[-1]]]
        if b'post outing himself.' in original:
            local.append([original.index(b'post outing himself.')+len(b'post outing himself')-1])
        changes=[c for c in layout['changes'] if c['kind']=='space' and c['paragraph']==p]
        for group in local:
            mapped=[]
            for pos in group:
                shift=sum(len(bytes.fromhex(c['replacement_hex']))-1 for c in changes if c['site']<pos)
                mapped.append(offset+pos+shift)
            groups.append(mapped)
        offset += len(original)+sum(len(bytes.fromhex(c['replacement_hex']))-1 for c in changes)
        if p<9:
            join=next((bytes.fromhex(c['replacement_hex']) for c in layout['changes']
                       if c['kind']=='join' and c['site']==p),bytes.fromhex(layout['base_join_hex']))
            offset += len(join)
    assert offset==len(source)
    assert len(groups)==(21 if case_mode=='independent' else 11)
    positions=sorted({x for g in groups for x in g})
    assert len(positions)==21
    lookup={pos:i for i,pos in enumerate(positions)}
    bitmasks=[sum(1<<lookup[p] for p in group) for group in groups]
    return source, positions, bitmasks


def expanded_mask(mask, bitmasks):
    out=0
    for bit, value in enumerate(bitmasks):
        if mask & 1 << bit:
            out ^= value
    return out


def serializer_checks(descriptors, case_mode):
    rng=random.Random(777)
    checks=0
    for layout in descriptors:
        source,positions,bits=prepared(layout,case_mode)
        for mask in [0,(1<<len(bits))-1,rng.randrange(1<<len(bits))]:
            out=bytearray(source)
            for bit,pos in enumerate(positions):
                if expanded_mask(mask,bits) & 1 << bit:
                    out[pos] ^= 32
            assert bytes(out)==reference(layout,mask,case_mode)
            checks+=1
    return checks


def run(args):
    from bip_utils import Base58Decoder, Bip32Secp256k1
    from bip39_gpu.gpu.bip32_gpu import base58check_encode, hash160_to_p2pkh
    indices=[int(x) for x in args.indices.split(',')]
    if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices):
        raise ValueError('Use distinct nonhardened indices')
    descriptors=layouts(args.family,args.defects)
    checks=serializer_checks(descriptors,args.case_mode)
    if args.verify_only:
        print(json.dumps(dict(serializer_checks=checks,layouts=len(descriptors),case_mode=args.case_mode)))
        return
    wallet=J.Wallet(args.platform,indices)
    np=wallet.np
    target_hash=Base58Decoder.CheckDecode(TARGET)[1:]
    config=dict(family='joint-example-layout-case-v1',layout_family=args.family,defects=args.defects,
                case_mode=args.case_mode,filter=args.prefix,indices=indices,target=TARGET,parent=PARENT,
                language='english',entropy='raw-md5',passphrase='',layout_count=len(descriptors),
                question_sha256=hashlib.sha256(QUESTION).hexdigest(),
                descriptor_sha256=hashlib.sha256(json.dumps(descriptors,sort_keys=True).encode()).hexdigest(),
                crypto_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),wallet_kernel_sha256=wallet.gpu.kernel_sha256,
                source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                    Path(__file__),ROOT/'aoi-posts-archive.json',ROOT/'assumptions-2026-09-27/quoted-mask-search.py',
                    ROOT/'assumptions-2026-09-27/quoted-mask.cl',ROOT/'expanded-2026-09-26/mask_md5_gpu.py',
                    ROOT/'expanded-2026-09-26/mask-md5.cl',ROOT/'pair-md5.cl',ROOT/'joint-format-2026-09-28/search.py',
                    ROOT/'joint-format-2026-09-28/checkpoint_io.py',ROOT/'assumptions-2026-09-27/search-assumptions.py',
                    ROOT/'followup-2026-09-26/language-settings-gpu.py',ROOT/'gpu-case-pairs.py',
                    ROOT/'expanded-2026-09-26/wallet_paths_gpu.py']})
    tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    dest=HERE/f'joint-example-{args.family}-{args.case_mode}-{args.prefix}-{tag}.json'
    per_layout=1<<(21 if args.case_mode=='independent' else 11)
    total=per_layout*len(descriptors)
    with J.exclusive(dest.with_suffix('.lock')):
        state=json.loads(dest.read_bytes()) if dest.exists() else dict(configuration=config,next_rank=0,
            candidates_total=total,derived_entropies=0,derived_addresses=0,matches=[],complete=False,
            elapsed_seconds=0.0,serializer_checks=checks,md5_checks=0,sampled_cpu_comparisons=0)
        if state['configuration']!=config or state['candidates_total']!=total:
            raise RuntimeError('Checkpoint identity mismatch')
        if state['complete'] or state['matches']:
            print(f'Already finished: {dest.name}',flush=True)
            return
        stop=min(total,state['next_rank']+args.limit) if args.limit else total
        begin=last=time.monotonic()
        initial_time=state['elapsed_seconds']
        initial_comparisons=state['sampled_cpu_comparisons']
        cached=None
        md5=None
        print(f'{dest.name}: {state["next_rank"]:,}/{total:,} text operations; '
              f'{len(descriptors):,} layouts x {per_layout:,} case choices; prefix={args.prefix}',flush=True)
        while state['next_rank']<stop:
            rank=state['next_rank']
            d,mask_start=divmod(rank,per_layout)
            size=min(args.batch,per_layout-mask_start,stop-rank)
            if cached!=d:
                source,positions,bitmasks=prepared(descriptors[d],args.case_mode)
                md5=Q.FilteredMasks(wallet.gpu.ctx,source,positions)
                # Changed length/byte offsets require new fixtures, including
                # zero/all/single-bit/random masks. Every later survivor is
                # independently checked, not only these initial fixtures.
                state['md5_checks']+=md5.base.certify()
                if cached is None:
                    state['md5_checks']+=md5.certify()
                cached=d
            if args.case_mode=='independent':
                # Role-order differs from byte-order when 'himself' is interior.
                # Enumerating ALL masks is invariant to this permutation.
                if args.prefix=='none':
                    masks=np.arange(mask_start,mask_start+size,dtype=np.uint64)
                    rows=list(zip(map(int,masks),md5.base.batch(masks)))
                else:
                    rows=md5.batch(mask_start,size,args.prefix)
                def witness(mask):
                    return md5.base.witness(mask)
            else:
                masks=np.asarray([expanded_mask(m,bitmasks) for m in range(mask_start,mask_start+size)],dtype=np.uint64)
                rows=[(mask_start+k,e) for k,e in enumerate(md5.base.batch(masks))
                      if args.prefix=='none' or e.hex().startswith(args.prefix)]
                def witness(mask):
                    return reference(descriptors[d],mask,args.case_mode)
            if rows:
                entropy=[e for _,e in rows]
                for mask,e in rows:
                    assert hashlib.md5(witness(mask)).digest()==e, 'Survivor MD5 fails independent validation'
                state['md5_checks']+=len(rows)
                words,seeds,out=wallet.derive(entropy,indices)
                sample=sorted({0,len(entropy)//2,len(entropy)-1})
                wallet.compare(words,seeds,out,[(k,entropy[k]) for k in sample],indices)
                for r in np.flatnonzero(np.all(out[0]==np.frombuffer(target_hash,dtype=np.uint8),axis=1)):
                    k,j=divmod(int(r),len(indices))
                    exact=witness(rows[k][0])
                    assert hashlib.md5(exact).digest()==entropy[k]
                    seed=hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
                    path=f'{PARENT}/{indices[j]}'
                    node=Bip32Secp256k1.FromSeed(seed).DerivePath(path)
                    pub=node.PublicKey().RawCompressed().ToBytes()
                    address=hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())
                    assert address==TARGET
                    found=HERE/f'FOUND-joint-example-{tag}.txt'
                    found.write_bytes(exact)
                    atomic_json(found.with_suffix('.json'),dict(address=address,path=path,md5=entropy[k].hex(),
                        mnemonic=words[k],private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),
                        layout=descriptors[d],mask=rows[k][0],configuration=config))
                    state['matches'].append(dict(address=address,file=found.name))
                state['derived_entropies']+=len(rows)
                state['derived_addresses']+=len(rows)*len(indices)
            state['next_rank']+=size
            state['complete']=state['next_rank']==total
            state['elapsed_seconds']=initial_time+time.monotonic()-begin
            state['sampled_cpu_comparisons']=initial_comparisons+wallet.comparisons
            state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
            atomic_json(dest,state)
            now=time.monotonic()
            if now-last>=20 or state['next_rank']==stop or state['matches']:
                print(json.dumps({k:state[k] for k in ['next_rank','candidates_total','derived_entropies',
                    'derived_addresses','complete','elapsed_seconds','matches']}),flush=True)
                last=now
            if state['matches']:
                print(f'CPU VERIFIED MATCH; saved locally: {found}',flush=True)
                return


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--family',choices=['boundaries','wordspaces'],default='boundaries')
    ap.add_argument('--defects',type=int,choices=[1,2],default=2)
    ap.add_argument('--case-mode',choices=['independent','paired'],default='independent')
    ap.add_argument('--prefix',choices=['3c6','none'],default='3c6')
    ap.add_argument('--indices',default='0,1,2,3,4,5,6')
    ap.add_argument('--platform',type=int,default=1)
    ap.add_argument('--batch',type=int,default=1048576)
    ap.add_argument('--limit',type=int,help='Maximum additional text ranks, then checkpoint and stop')
    ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args()
    if sys.flags.optimize:
        ap.error('Python -O disables required verification')
    if args.batch<1 or (args.limit is not None and args.limit<1):
        ap.error('Positive batch/limit required')
    if args.case_mode=='paired' and args.batch>16384:
        args.batch=16384
    run(args)


if __name__=='__main__':
    main()
