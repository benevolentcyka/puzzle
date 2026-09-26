"""Calibrate historical entropy conversion after direct-address negatives.

Try every paragraph-boundary case pattern (including the named 'himself' F),
retain MD5 hints with at most the requested number of wrong prefix digits,
then use historical Coleman fixed-word-count entropy conversion. These are
SHA256(ASCII lower/upper MD5 hex), truncated to 16/20/24/28/32 bytes.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
TARGET='1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'
H160=bytes.fromhex('09d565074752019721ce68c58548ebc13750d5cc')


def atomic_json(path,value):
    tmp=path.with_suffix('.json.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dependency',type=Path,default=ROOT/'bip39-gpu-review')
    parser.add_argument('--prefix-errors',type=int,choices=[0,1],default=0)
    parser.add_argument('--indices',default=','.join(map(str,range(21))))
    parser.add_argument('--platform',type=int,default=1)
    parser.add_argument('--batch',type=int,default=16384)
    args=parser.parse_args();indices=[int(x) for x in args.indices.split(',')]
    sys.path.insert(0,str(args.dependency/'src'))
    spec=importlib.util.spec_from_file_location('certifier',ROOT/'gpu-case-pairs.py')
    cert=importlib.util.module_from_spec(spec);spec.loader.exec_module(cert)
    from bip39_gpu.core.mnemonic import BIP39Mnemonic
    from bip39_gpu.gpu import context,pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs,hash160_to_p2pkh
    context._global_context=context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback=cert.die_fallback
    cert.certify_gpu(indices[0]);cert.certify_gpu(indices[-1])
    def seeds_for(words):
        passwords=[w.encode('utf8') for w in words]
        # HMAC hashes keys longer than its 128-byte block. The pinned GPU
        # kernel requires short keys, so perform that exact preprocessing.
        passwords=[hashlib.sha512(p).digest() if len(p)>128 else p for p in passwords]
        return pbkdf2_gpu.pbkdf2_hmac_sha512_gpu(passwords,[b'mnemonic']*len(words))
    vectors=[hashlib.sha256(f'converter-seed-regression-{i}'.encode()).digest()[:[16,20,24,28,32][i%5]] for i in range(256)]
    words=[str(BIP39Mnemonic.from_entropy(e)) for e in vectors]
    seeds=seeds_for(words)
    for i,w in enumerate(words):
        if seeds[i]!=hashlib.pbkdf2_hmac('sha512',w.encode(),b'mnemonic',2048,64):
            raise RuntimeError(f'Independent PBKDF2 mismatch at entropy-length vector {i}')
    print('256 independent short/long mnemonic seed comparisons passed.',flush=True)
    historical=(HERE/'verification/iancoleman-2019-index.js').read_text()
    assert 'sjcl.hash.sha256.hash(entropy.cleanStr)' in historical
    assert 'var numberOfBits = 32 * mnemonicLength / 3;' in historical
    posts=json.loads((ROOT/'aoi-posts-archive.json').read_text())
    q=next(x for x in posts if x['id']=='cleczc')['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0]
    assert hashlib.md5(q.encode()).hexdigest().startswith('7759227')
    ps=q.split('\n\n');bases=[];entries=[];enumerated=0;survivors=0
    stream=hashlib.sha256();begin=time.perf_counter()
    for join,separator in [('lf','\n\n'),('crlf','\r\n\r\n')]:
        source=separator.join(ps).encode('ascii');positions=[];offset=0
        for p in ps:
            letters=[i for i,c in enumerate(p) if c.isascii() and c.isalpha()]
            positions.extend([offset+letters[0],offset+letters[-1]])
            if 'post outing himself.' in p:positions.append(offset+p.index('post outing himself.')+len('post outing himself')-1)
            offset+=len(p)+len(separator)
        positions=sorted(set(positions));assert len(positions)==21
        saved=json.loads((HERE/f'example-unfiltered-published-{join}-index0.json').read_text())
        assert saved['source_sha256']==hashlib.sha256(source).hexdigest() and saved['offsets']==positions and saved['complete']
        bases.append((join,source,positions));work=bytearray(source);last=0
        for rank in range(1<<len(positions)):
            mask=rank^(rank>>1);changed=last^mask
            while changed:
                bit=changed&-changed;work[positions[bit.bit_length()-1]]^=32;changed^=bit
            last=mask;h=hashlib.md5(work).digest();enumerated+=1
            digits=(h[0]>>4,h[0]&15,h[1]>>4)
            errors=sum(a!=b for a,b in zip(digits,(3,12,6)))
            if errors>args.prefix_errors:continue
            survivors+=1
            for casing in ['lower','upper']:
                md=h.hex() if casing=='lower' else h.hex().upper()
                converted=hashlib.sha256(md.encode('ascii')).digest()
                for length in [16,20,24,28,32]:
                    entropy=converted[:length];label=(join,rank,mask,h.hex(),casing,length,errors)
                    stream.update(entropy);stream.update(json.dumps(label).encode()+b'\n');entries.append((entropy,label))
        print(f'{join}: enumerated={enumerated:,}, prefix survivors={survivors:,}',flush=True)
    stream_sha=stream.hexdigest();kernel=cert.gpu_kernel_fingerprint()
    state_path=HERE/f'example-converter-prefix-errors{args.prefix_errors}.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else None
    if state and (state['candidate_stream_sha256']!=stream_sha or state['gpu_kernel_sha256']!=kernel or state['indices']!=indices):
        raise RuntimeError('Checkpoint stream, kernels or indices differ')
    rank=state['next_rank'] if state else 0;initial=rank
    while rank<len(entries):
        batch=entries[rank:rank+args.batch];entropies=[e for e,_ in batch]
        words=[str(BIP39Mnemonic.from_entropy(e)) for e in entropies];seeds=seeds_for(words)
        for index in indices:
            output=batch_seed_to_gpu_outputs(seeds,address_index=index)
            if output is None:raise RuntimeError('GPU unavailable; CPU fallback refused')
            hashes,_,_=output
            for k in sorted({0,len(batch)//2,len(batch)-1}):
                expected,_=cert.cpu_address(entropies[k],index)
                if hash160_to_p2pkh(hashes[k])!=expected:raise RuntimeError(f'CPU/GPU disagreement at {rank+k}, index {index}')
            for k,h in enumerate(hashes):
                if h!=H160:continue
                expected,mnemonic=cert.cpu_address(entropies[k],index)
                if expected!=TARGET:raise RuntimeError('Hit failed independent CPU validation')
                entropy,label=batch[k];join,text_rank,mask,md,casing,length,errors=label
                _,source,positions=next(b for b in bases if b[0]==join);witness=bytearray(source)
                for bit,pos in enumerate(positions):
                    if mask&(1<<bit):witness[pos]^=32
                assert hashlib.md5(witness).hexdigest()==md
                dest=HERE/f'FOUND-example-converter-errors{args.prefix_errors}.txt';dest.write_bytes(witness)
                atomic_json(dest.with_suffix('.json'),{'address':expected,'mnemonic':mnemonic,'index':index,'entropy':entropy.hex(),
                    'md5':md,'join':join,'rank':text_rank,'mask':mask,'ascii_md5_casing':casing,'entropy_bytes':length,'prefix_errors':errors})
                print(f'VERIFIED MATCH {dest}',flush=True);return
        rank+=len(batch)
        atomic_json(state_path,{'target':TARGET,'enumerated_texts':enumerated,'prefix_survivors':survivors,
            'allowed_prefix_errors':args.prefix_errors,'indices':indices,'seed_regression_vectors':256,
            'candidate_stream_sha256':stream_sha,'gpu_kernel_sha256':kernel,'next_rank':rank,'candidates_total':len(entries),
            'derived_addresses':rank*len(indices),'complete':rank==len(entries),'matches':0,
            'elapsed_seconds':time.perf_counter()-begin,'updated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
        print(f'converted={rank:,}/{len(entries):,}, addresses={rank*len(indices):,}; no match',flush=True)


if __name__=='__main__':main()
