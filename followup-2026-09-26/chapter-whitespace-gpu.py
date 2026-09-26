"""Check the final chapter after assuming the two-case-toggle family fails.

Independently trim each of the 13 paragraphs with saved trailing spaces.
Combine with every selection of the four FFWW groups, both paragraph joins,
two NBSP choices, and retained LF versus normalized CRLF internal breaks.
This edits source serialization, not additional capitalization positions.
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
GROUPS=[[4,5,6,7],[92,93,94,95],[167,168,169,170],[230,231,232,234]]
ADDRESSES=['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W','1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']


def atomic_json(path,value):
    temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)


def flip(p):
    chars=list(p);letters=[i for i,c in enumerate(chars) if c.isascii() and c.isalpha()]
    chars[letters[0]]=chars[letters[0]].lower();chars[letters[-1]]=chars[letters[-1]].upper()
    return ''.join(chars)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dependency',type=Path,default=ROOT/'bip39-gpu-review')
    parser.add_argument('--indices',default='0,1,2,3,4,5,6')
    parser.add_argument('--batch',type=int,default=32768)
    parser.add_argument('--limit',type=int,default=100000)
    parser.add_argument('--all',action='store_true')
    parser.add_argument('--platform',type=int,default=1)
    args=parser.parse_args();indices=[int(x) for x in args.indices.split(',')]
    if not indices or any(i<0 for i in indices) or len(set(indices))!=len(indices):parser.error('Use distinct nonnegative indices')
    sys.path.insert(0,str(args.dependency/'src'))
    spec=importlib.util.spec_from_file_location('certifier',ROOT/'gpu-case-pairs.py')
    cert=importlib.util.module_from_spec(spec);spec.loader.exec_module(cert)
    from bip39_gpu.core.mnemonic import BIP39Mnemonic
    from bip39_gpu.gpu import context,pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs,hash160_to_p2pkh
    from bip_utils import Base58Decoder,Bip39SeedGenerator,Bip44,Bip44Coins,Bip44Changes
    targets={Base58Decoder.CheckDecode(a)[1:]:a for a in ADDRESSES}
    assert all(hash160_to_p2pkh(h)==a for h,a in targets.items())
    source_path=ROOT/'wattpad-paragraphs.json';paras=json.loads(source_path.read_text(encoding='utf8'))
    trailing=[i for i,p in enumerate(paras) if p.endswith(' ')]
    assert trailing==[85,107,121,127,138,146,164,165,191,200,208,219,266]
    assert len(paras)==273 and sum(p.count('\n') for p in paras)==10 and sum(p.count('\u00a0') for p in paras)==6
    shapes=[]
    for mask in range(16):
        selected={i for bit,g in enumerate(GROUPS) if mask&(1<<bit) for i in g}
        case_paras=[flip(p) if i in selected else p for i,p in enumerate(paras)]
        for join in ['lf','crlf']:
            for nbsp in ['retain','space']:
                for br in ['lf','crlf']:
                    ps=[p.replace('\u00a0',' ') if nbsp=='space' else p for p in case_paras]
                    if br=='crlf':ps=[p.replace('\n','\r\n') for p in ps]
                    encoded=[p.encode('utf8') for p in ps]
                    shapes.append({'group_mask':mask,'join':join,'nbsp':nbsp,'internal_break':br,'paragraphs':encoded,
                                   'trimmed':[p.rstrip(b' ') for p in encoded],'separator':b'\n\n' if join=='lf' else b'\r\n\r\n'})
    def candidate(rank):
        shape,mask=divmod(rank,1<<len(trailing));s=shapes[shape]
        ps=list(s['paragraphs'])
        for bit,i in enumerate(trailing):
            if mask&(1<<bit):ps[i]=s['trimmed'][i]
        return s['separator'].join(ps),{'group_mask':s['group_mask'],'join':s['join'],'nbsp':s['nbsp'],
            'internal_break':s['internal_break'],'trim_mask':mask,'trimmed_paragraphs':[i for bit,i in enumerate(trailing) if mask&(1<<bit)]}
    total=len(shapes)*(1<<len(trailing));assert total==1048576
    source_sha=hashlib.sha256(source_path.read_bytes()).hexdigest();kernel=cert.gpu_kernel_fingerprint()
    state_path=HERE/('chapter-whitespace-indices'+'-'.join(map(str,indices))+'.json')
    state=json.loads(state_path.read_text()) if state_path.exists() else None
    if state and (state['source_sha256']!=source_sha or state['gpu_kernel_sha256']!=kernel or state['indices']!=indices):
        raise RuntimeError('Checkpoint source, kernels or indices differ')
    rank=state['next_rank'] if state else 0;initial=rank;stop=total if args.all else min(total,rank+args.limit)
    if rank==total:print('Already completed this chapter whitespace family.',flush=True);return
    context._global_context=context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback=cert.die_fallback
    for index in indices:cert.certify_gpu(index)
    begin=time.perf_counter();print(f'Chapter whitespace: ranks=[{rank:,},{stop:,}), indices={indices}',flush=True)
    while rank<stop:
        size=min(args.batch,stop-rank)
        entropies=[hashlib.md5(candidate(r)[0]).digest() for r in range(rank,rank+size)]
        words=[str(BIP39Mnemonic.from_entropy(h)) for h in entropies]
        seeds=pbkdf2_gpu.batch_mnemonic_to_seed_gpu(words)
        for index in indices:
            output=batch_seed_to_gpu_outputs(seeds,address_index=index)
            if output is None:raise RuntimeError('GPU BIP32 unavailable; CPU fallback refused')
            hashes,_,_=output
            if len(hashes)!=size:raise RuntimeError('GPU output count mismatch')
            for k in sorted({0,size//2,size-1}):
                expected,_=cert.cpu_address(entropies[k],index)
                if hash160_to_p2pkh(hashes[k])!=expected:raise RuntimeError(f'CPU/GPU mismatch rank {rank+k}, index {index}')
            for k,h in enumerate(hashes):
                if h not in targets:continue
                expected,mnemonic=cert.cpu_address(entropies[k],index)
                if expected!=targets[h]:raise RuntimeError('Potential match failed independent CPU validation')
                text,label=candidate(rank+k);assert hashlib.md5(text).digest()==entropies[k]
                dest=HERE/f'FOUND-chapter-whitespace-{index}.txt';dest.write_bytes(text)
                node=Bip44.FromSeed(Bip39SeedGenerator(mnemonic).Generate(),Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
                atomic_json(dest.with_suffix('.json'),{'address':expected,'md5':entropies[k].hex(),'mnemonic':mnemonic,
                    'index':index,'private_wif':node.PrivateKey().ToWif(),'rank':rank+k,'label':label})
                print(f'VERIFIED MATCH: {dest}',flush=True);return
        rank+=size
        atomic_json(state_path,{'targets':ADDRESSES,'source_sha256':source_sha,'gpu_kernel_sha256':kernel,'indices':indices,
            'next_rank':rank,'candidates_total':total,'derived_addresses':rank*len(indices),'complete':rank==total,'matches':0,
            'trailing_paragraphs':trailing,'shapes':len(shapes),'prefix_filter_used':False,
            'last_run_speed':(rank-initial)/(time.perf_counter()-begin),'updated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
        print(f'checked={rank:,}/{total:,} speed={(rank-initial)/(time.perf_counter()-begin):,.0f}/s; no match',flush=True)


if __name__=='__main__':main()
