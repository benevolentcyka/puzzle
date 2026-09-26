"""Directly check single copy/edit errors in the solved format example.

No MD5-prefix filter. Preserve the full question, apply the known FFWW case
rule, then replace/insert/delete one character or transpose adjacent bytes.
The bounded alphabet is printable ASCII plus common copied-text artifacts.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
TARGET='1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'
H160=bytes.fromhex('09d565074752019721ce68c58548ebc13750d5cc')
CHARS=[chr(i) for i in range(32,127)]+['\t','\r','\n','\u00a0','\u200b','\ufeff','\u2019','\u201c','\u201d','\u2013','\u2014']


def atomic_json(path,data):
    temp=path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
    temp.replace(path)


def edit_at(source,rank):
    n=len(source); alphabet=len(CHARS)
    if rank<n*alphabet:
        offset,char=divmod(rank,alphabet)
        return source[:offset]+CHARS[char].encode()+source[offset+1:],{'op':'replace','offset':offset,'char':CHARS[char]}
    rank-=n*alphabet
    if rank<(n+1)*alphabet:
        offset,char=divmod(rank,alphabet)
        return source[:offset]+CHARS[char].encode()+source[offset:],{'op':'insert','offset':offset,'char':CHARS[char]}
    rank-=(n+1)*alphabet
    if rank<n:
        return source[:rank]+source[rank+1:],{'op':'delete','offset':rank}
    rank-=n
    return source[:rank]+source[rank+1:rank+2]+source[rank:rank+1]+source[rank+2:],{'op':'transpose','offset':rank}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dependency',type=Path,default=ROOT/'bip39-gpu-review')
    parser.add_argument('--draft',choices=['published','removed','split'],default='published')
    parser.add_argument('--join',choices=['lf','crlf'],default='lf')
    parser.add_argument('--case',choices=['ffww','raw','ffww-himself'],default='ffww')
    parser.add_argument('--indices',default='0,1')
    parser.add_argument('--limit',type=int,default=100000)
    parser.add_argument('--all',action='store_true')
    parser.add_argument('--batch',type=int,default=32768)
    parser.add_argument('--platform',type=int,default=1)
    args=parser.parse_args()
    indices=[int(x) for x in args.indices.split(',')]
    if not indices or any(i<0 for i in indices) or len(set(indices))!=len(indices):
        parser.error('indices must be distinct nonnegative integers')
    sys.path.insert(0,str(args.dependency/'src'))
    spec=importlib.util.spec_from_file_location('certifier',ROOT/'gpu-case-pairs.py')
    cert=importlib.util.module_from_spec(spec);spec.loader.exec_module(cert)
    from bip39_gpu.core.mnemonic import BIP39Mnemonic
    from bip39_gpu.gpu import context,pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs,hash160_to_p2pkh
    posts=json.loads((ROOT/'aoi-posts-archive.json').read_text())
    q=next(x for x in posts if x['id']=='cleczc')['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0]
    assert hashlib.md5(q.encode()).hexdigest().startswith('7759227')
    ps=q.split('\n\n')
    extra=' Even after I explained the method used and the result in detail.'
    if args.draft=='removed':ps=[p.replace(extra,'') for p in ps]
    if args.draft=='split':ps=[piece for p in ps for piece in ([p.replace(extra,''),extra.strip()] if extra in p else [p])]
    if args.case!='raw':
        for i,p in enumerate(ps):
            if p[0] not in 'FW':continue
            chars=list(p);letters=[j for j,c in enumerate(chars) if c.isascii() and c.isalpha()]
            chars[letters[0]]=chars[letters[0]].lower();chars[letters[-1]]=chars[letters[-1]].upper()
            ps[i]=''.join(chars)
    if args.case=='ffww-himself':
        for i,p in enumerate(ps):
            if 'post outing himself.' in p:ps[i]='i'+p[1:].replace('post outing himself.','post outing himselF.')
    source=('\n\n' if args.join=='lf' else '\r\n\r\n').join(ps).encode('ascii')
    sha=hashlib.sha256(source).hexdigest();kernel=cert.gpu_kernel_fingerprint()
    total=len(source)*len(CHARS)+(len(source)+1)*len(CHARS)+len(source)+len(source)-1
    label=f'{args.draft}-{args.join}-{args.case}-indices'+ '-'.join(map(str,indices))
    state_path=HERE/f'example-edit-{label}.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else None
    if state and (state['source_sha256']!=sha or state['gpu_kernel_sha256']!=kernel or state['alphabet']!=CHARS or state['indices']!=indices):
        raise RuntimeError('Checkpoint differs from source, kernels, alphabet or indices')
    rank=state['next_rank'] if state else 0;initial=rank
    stop=total if args.all else min(total,rank+args.limit)
    if rank==total:print(f'Already complete: {label}',flush=True);return
    context._global_context=context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback=cert.die_fallback
    for index in indices:cert.certify_gpu(index)
    begin=time.perf_counter()
    print(f'{label} candidates=[{rank:,},{stop:,})',flush=True)
    while rank<stop:
        size=min(args.batch,stop-rank)
        entropies=[hashlib.md5(edit_at(source,r)[0]).digest() for r in range(rank,rank+size)]
        words=[str(BIP39Mnemonic.from_entropy(h)) for h in entropies]
        seeds=pbkdf2_gpu.batch_mnemonic_to_seed_gpu(words)
        for index in indices:
            output=batch_seed_to_gpu_outputs(seeds,address_index=index)
            if output is None:raise RuntimeError('GPU unavailable; CPU fallback refused')
            hashes,_,_=output
            if len(hashes)!=size:raise RuntimeError('GPU output count mismatch')
            for k in sorted({0,size//2,size-1}):
                expected,_=cert.cpu_address(entropies[k],index)
                if hash160_to_p2pkh(hashes[k])!=expected:raise RuntimeError(f'CPU/GPU disagreement at {rank+k}, index {index}')
            for k,h in enumerate(hashes):
                if h!=H160:continue
                expected,mnemonic=cert.cpu_address(entropies[k],index)
                if expected!=TARGET:raise RuntimeError('Potential hit failed CPU confirmation')
                witness,edit=edit_at(source,rank+k)
                assert hashlib.md5(witness).digest()==entropies[k]
                dest=HERE/f'FOUND-example-edit-{label}.txt';dest.write_bytes(witness)
                atomic_json(dest.with_suffix('.json'),{'address':expected,'md5':entropies[k].hex(),'mnemonic':mnemonic,'index':index,'edit':edit,'rank':rank+k,'source_sha256':sha,'published_prefix_matches':entropies[k].hex().startswith('3c6')})
                print(f'VERIFIED MATCH {dest}',flush=True);return
        rank+=size
        atomic_json(state_path,{'target':TARGET,'source_sha256':sha,'gpu_kernel_sha256':kernel,'alphabet':CHARS,'indices':indices,'draft':args.draft,'join':args.join,'case':args.case,'next_rank':rank,'candidates_total':total,'derived_addresses':rank*len(indices),'complete':rank==total,'matches':0,'prefix_filter_used':False,'last_run_speed':(rank-initial)/(time.perf_counter()-begin),'updated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
        print(f'checked={rank:,}/{total:,} speed={(rank-initial)/(time.perf_counter()-begin):,.0f}/s; no match',flush=True)


if __name__=='__main__':main()
