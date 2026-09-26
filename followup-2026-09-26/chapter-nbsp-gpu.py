"""Post-pair investigation: independently preserve, space, or delete six NBSPs.

Combine all 729 NBSP choices with the 16 sign-group selections, three title
boundaries, LF/CRLF joins and internal breaks, optional terminal newline,
and preserved versus globally trimmed paragraph trailing spaces. This checks
raw MD5/BIP39 English against both escrows at indices 0..20, without a filter.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
GROUPS=[[4,5,6,7],[92,93,94,95],[167,168,169,170],[230,231,232,234]]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--indices',default=','.join(map(str,range(21))))
    parser.add_argument('--platform',type=int,default=1);parser.add_argument('--batch',type=int,default=16384)
    parser.add_argument('--limit',type=int,default=100000);parser.add_argument('--all',action='store_true')
    parser.add_argument('--dependency',type=Path,default=ROOT/'bip39-gpu-review');args=parser.parse_args()
    indices=[int(x) for x in args.indices.split(',')]
    if not indices or len(set(indices))!=len(indices) or any(i<0 for i in indices):parser.error('Use distinct nonnegative indices')
    sys.path.insert(0,str(args.dependency/'src'))
    spec=importlib.util.spec_from_file_location('certifier',ROOT/'gpu-case-pairs.py');cert=importlib.util.module_from_spec(spec);spec.loader.exec_module(cert)
    from bip39_gpu.core.mnemonic import BIP39Mnemonic
    from bip39_gpu.gpu import context,pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs,hash160_to_p2pkh
    from bip_utils import Base58Decoder
    source=ROOT/'wattpad-paragraphs.json';paras=json.loads(source.read_text(encoding='utf8'))
    assert len(paras)==273 and sum(p.count('\u00a0') for p in paras)==6
    shapes=[]
    for group_mask in range(16):
        selected={i for bit,g in enumerate(GROUPS) if group_mask&(1<<bit) for i in g}
        modified=[]
        for i,p in enumerate(paras):
            if i in selected:
                chars=list(p);letters=[j for j,c in enumerate(chars) if c.isascii() and c.isalpha()]
                chars[letters[0]]=chars[letters[0]].lower();chars[letters[-1]]=chars[letters[-1]].upper();p=''.join(chars)
            modified.append(p)
        for start in [0,1,3]:
            for trim in [False,True]:
                for join,sep in [('lf','\n\n'),('crlf','\r\n\r\n')]:
                    for tail in ['',sep[:len(sep)//2]]:
                        ps=[p.rstrip(' ') if trim else p for p in modified[start:]]
                        if join=='crlf':ps=[p.replace('\n','\r\n') for p in ps]
                        encoded=(sep.join(ps)+tail).encode('utf8');pieces=encoded.split(b'\xc2\xa0');assert len(pieces)==7
                        label={'group_mask':group_mask,'start':start,'trim_trailing_spaces':trim,'join':join,'tail':tail}
                        prefix=hashlib.md5(pieces[0]);shapes.append((pieces,prefix,label))
    assert len(shapes)==384;total=len(shapes)*729
    def candidate(rank,witness=False):
        shape,mask=divmod(rank,729);pieces,prefix,label=shapes[shape];md=prefix.copy();segments=[pieces[0]];choices=[]
        for part in pieces[1:]:
            choice=mask%3;mask//=3;edit=[b'\xc2\xa0',b' ',b''][choice];choices.append(choice)
            md.update(edit);md.update(part)
            if witness:segments.extend([edit,part])
        return md.digest(),dict(label,nbsp_choices=choices),b''.join(segments) if witness else None
    state_path=HERE/('chapter-nbsp-indices'+'-'.join(map(str,indices))+'.json');source_sha=hashlib.sha256(source.read_bytes()).hexdigest();kernel=cert.gpu_kernel_fingerprint()
    old=json.loads(state_path.read_text()) if state_path.exists() else None
    if old and any(old[k]!=v for k,v in {'source_sha256':source_sha,'gpu_kernel_sha256':kernel,'indices':indices}.items()):raise RuntimeError('Checkpoint inputs differ')
    rank=old['next_rank'] if old else 0;initial=rank;stop=total if args.all else min(total,rank+args.limit)
    if rank==total:print('Already completed the mixed NBSP family.',flush=True);return
    context._global_context=context.GPUContext(platform_id=args.platform);pbkdf2_gpu._pbkdf2_cpu_fallback=cert.die_fallback
    cert.certify_gpu(indices[0]);cert.certify_gpu(indices[-1])
    targets=['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W','1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC'];target_hashes={Base58Decoder.CheckDecode(a)[1:]:a for a in targets}
    begin=time.perf_counter();print(f'Mixed NBSP: ranks=[{rank:,},{stop:,}), shapes={len(shapes)}, indices={indices}',flush=True)
    while rank<stop:
        size=min(args.batch,stop-rank);entropies=[candidate(r)[0] for r in range(rank,rank+size)]
        words=[str(BIP39Mnemonic.from_entropy(e)) for e in entropies];seeds=pbkdf2_gpu.batch_mnemonic_to_seed_gpu(words)
        sampled=sorted({0,size//2,size-1})
        for k in sampled:
            md,_,text=candidate(rank+k,True)
            if hashlib.md5(text).digest()!=md or md!=entropies[k]:raise RuntimeError('Independent NBSP serializer/MD5 mismatch')
        for index in indices:
            output=batch_seed_to_gpu_outputs(seeds,address_index=index)
            if output is None:raise RuntimeError('GPU unavailable; refusing fallback')
            hashes=output[0]
            for k in sampled:
                expected,_=cert.cpu_address(entropies[k],index)
                if hash160_to_p2pkh(hashes[k])!=expected:raise RuntimeError('Sampled independent address mismatch')
            for k,h in enumerate(hashes):
                if h not in target_hashes:continue
                address,mnemonic=cert.cpu_address(entropies[k],index)
                if address!=target_hashes[h]:raise RuntimeError('Hit failed independent CPU validation')
                md,label,witness=candidate(rank+k,True);assert hashlib.md5(witness).digest()==md
                dest=HERE/f'FOUND-chapter-nbsp-index{index}.txt';dest.write_bytes(witness)
                cert.atomic_json(dest.with_suffix('.json'),{'address':address,'md5':md.hex(),'mnemonic':mnemonic,'index':index,'rank':rank+k,'label':label})
                print(f'VERIFIED MATCH {dest}',flush=True);return
        rank+=size
        cert.atomic_json(state_path,{'targets':targets,'source_sha256':source_sha,'gpu_kernel_sha256':kernel,'indices':indices,'shapes':len(shapes),'nbsp_choices_per_shape':729,'next_rank':rank,'candidates_total':total,'derived_addresses':rank*len(indices),'complete':rank==total,'matches':0,'prefix_filter_used':False,'elapsed_seconds':time.perf_counter()-begin,'updated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
        print(f'checked={rank:,}/{total:,}, addresses={rank*len(indices):,}; no match; speed={(rank-initial)/(time.perf_counter()-begin):,.0f}/s',flush=True)


if __name__=='__main__':main()
