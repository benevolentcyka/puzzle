"""Check file encodings and terminal newlines of the solved format example.

Every subset of its 21 boundary/documented case edits is hashed as UTF-8 with
BOM, UTF-16 LE/BE with or without BOM, and UTF-8 with one/two LF/CRLF tails.
The exact published MD5 prefix is required by default; --prefix-errors 1
allows one wrong hint digit. Test raw and all ten historical converter modes.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix-errors',type=int,choices=[0,1],default=0)
    p.add_argument('--indices',default=','.join(map(str,range(21))))
    p.add_argument('--platform',type=int,default=1);p.add_argument('--batch',type=int,default=16384)
    p.add_argument('--dependency',type=Path,default=ROOT/'bip39-gpu-review');args=p.parse_args()
    indices=[int(x) for x in args.indices.split(',')]
    if not indices or len(set(indices))!=len(indices) or any(i<0 for i in indices):p.error('Use distinct nonnegative indices')
    sys.path.insert(0,str(args.dependency/'src'))
    spec=importlib.util.spec_from_file_location('languages',HERE/'language-settings-gpu.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
    spec=importlib.util.spec_from_file_location('certifier',ROOT/'gpu-case-pairs.py');cert=importlib.util.module_from_spec(spec);spec.loader.exec_module(cert)
    from bip39_gpu.core.mnemonic import BIP39Mnemonic
    from bip39_gpu.gpu import context,pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs,hash160_to_p2pkh
    target='1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi';h160=bytes.fromhex('09d565074752019721ce68c58548ebc13750d5cc')
    context._global_context=context.GPUContext(platform_id=args.platform);pbkdf2_gpu._pbkdf2_cpu_fallback=cert.die_fallback
    cert.certify_gpu(indices[0]);cert.certify_gpu(indices[-1])
    posts=json.loads((ROOT/'aoi-posts-archive.json').read_text());q=next(x for x in posts if x['id']=='cleczc')['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0]
    assert hashlib.md5(q.encode()).hexdigest().startswith('7759227');shapes=[]
    for join,sep in [('lf','\n\n'),('crlf','\r\n\r\n')]:
        text=sep.join(q.split('\n\n'));positions=[];offset=0
        for para in q.split('\n\n'):
            letters=[i for i,c in enumerate(para) if c.isascii() and c.isalpha()];positions.extend([offset+letters[0],offset+letters[-1]])
            if 'post outing himself.' in para:positions.append(offset+para.index('post outing himself.')+len('post outing himself')-1)
            offset+=len(para)+len(sep)
        positions=sorted(set(positions));assert len(positions)==21
        for encoding,bom,tail in [('utf8',b'\xef\xbb\xbf',''),('utf-16-le',b'',''),('utf-16-be',b'',''),('utf-16-le',b'\xff\xfe',''),('utf-16-be',b'\xfe\xff','')]+[('utf8',b'',t) for t in ['\n','\n\n','\r\n','\r\n\r\n']]:
            width=1 if encoding=='utf8' else 2;byte_offset=1 if encoding=='utf-16-be' else 0
            byte_positions=[len(bom)+width*i+byte_offset for i in positions];source=bom+(text+tail).encode(encoding)
            assert all(chr(source[i]).isascii() and chr(source[i]).isalpha() for i in byte_positions)
            shapes.append((source,byte_positions,{'join':join,'encoding':encoding,'bom_hex':bom.hex(),'tail':tail}))
    entries=[];source_survivors=0;enumerated=0;stream=hashlib.sha256();begin=time.perf_counter()
    for source,positions,shape in shapes:
        work=bytearray(source);last=0;survivors=0
        for rank in range(1<<len(positions)):
            mask=rank^(rank>>1);changed=last^mask
            while changed:
                bit=changed&-changed;work[positions[bit.bit_length()-1]]^=32;changed^=bit
            last=mask;md=hashlib.md5(work).digest();enumerated+=1
            if sum(a!=b for a,b in zip((md[0]>>4,md[0]&15,md[1]>>4),(3,12,6)))>args.prefix_errors:continue
            survivors+=1;source_survivors+=1
            for mode,entropy in [('raw-128',md)]+[(f'fixed-{length*8}-{casing}',hashlib.sha256((md.hex() if casing=='lower' else md.hex().upper()).encode()).digest()[:length]) for casing in ['lower','upper'] for length in [16,20,24,28,32]]:
                label=dict(shape,rank=rank,mask=mask,md5=md.hex(),mode=mode,source_sha256=hashlib.sha256(source).hexdigest())
                entries.append((entropy,label,source,positions));stream.update(entropy);stream.update(json.dumps(label,sort_keys=True).encode())
        print(f'{shape}: {survivors:,} prefix survivors; total enumerated={enumerated:,}',flush=True)
    stream_sha=stream.hexdigest();kernel=cert.gpu_kernel_fingerprint();state_path=HERE/f'example-encoding-errors{args.prefix_errors}.json'
    old=json.loads(state_path.read_text()) if state_path.exists() else None
    if old and any(old[k]!=v for k,v in {'candidate_stream_sha256':stream_sha,'gpu_kernel_sha256':kernel,'indices':indices}.items()):raise RuntimeError('Checkpoint input differs')
    rank=old['next_rank'] if old else 0
    while rank<len(entries):
        batch=entries[rank:rank+args.batch];entropies=[x[0] for x in batch];words=[str(BIP39Mnemonic.from_entropy(e)) for e in entropies]
        seeds=pbkdf2_gpu.pbkdf2_hmac_sha512_gpu([L.normalized_password(w) for w in words],[b'mnemonic']*len(words))
        for index in indices:
            output=batch_seed_to_gpu_outputs(seeds,address_index=index)
            if output is None:raise RuntimeError('GPU unavailable; refusing fallback')
            hashes=output[0]
            for k in sorted({0,len(batch)//2,len(batch)-1}):
                expected,_=cert.cpu_address(entropies[k],index)
                if expected!=hash160_to_p2pkh(hashes[k]):raise RuntimeError('Independent sample address mismatch')
            for k,h in enumerate(hashes):
                if h!=h160:continue
                address,mnemonic=cert.cpu_address(entropies[k],index)
                if address!=target:raise RuntimeError('Hit failed independent validation')
                entropy,label,source,positions=batch[k];witness=bytearray(source)
                for bit,pos in enumerate(positions):
                    if label['mask']&(1<<bit):witness[pos]^=32
                assert hashlib.md5(witness).hexdigest()==label['md5']
                dest=HERE/f'FOUND-example-encoding-errors{args.prefix_errors}.txt';dest.write_bytes(witness)
                L.save(dest.with_suffix('.json'),{'address':address,'index':index,'entropy':entropy.hex(),'mnemonic':mnemonic,'label':label})
                print(f'VERIFIED MATCH {dest}',flush=True);return
        rank+=len(batch)
        L.save(state_path,{'target':target,'indices':indices,'allowed_prefix_errors':args.prefix_errors,'shapes':len(shapes),'enumerated_texts':enumerated,'prefix_survivors':source_survivors,'candidate_stream_sha256':stream_sha,'gpu_kernel_sha256':kernel,'next_rank':rank,'candidates_total':len(entries),'derived_addresses':rank*len(indices),'complete':rank==len(entries),'matches':0,'elapsed_seconds':time.perf_counter()-begin,'updated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
        print(f'checked={rank:,}/{len(entries):,}, addresses={rank*len(indices):,}; no match',flush=True)


if __name__=='__main__':main()
