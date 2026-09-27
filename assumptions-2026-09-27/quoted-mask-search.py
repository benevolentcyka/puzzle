"""All paragraph and quoted-token endpoint case choices in the solved example.

32 independent positions, 2**32 texts for each LF/CRLF join. Uses the declared
3c6 MD5 hint as a filter. It does not imply exhaustive coverage without that
hint or outside the English/raw/empty-passphrase BIP44 convention.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'expanded-2026-09-26'))
sys.path.insert(0, str(ROOT / 'bip39-gpu-review/src'))
from mask_md5_gpu import MaskMD5GPU
from wallet_paths_gpu import WalletPathsGPU
import numpy as np
import pyopencl as cl
spec = importlib.util.spec_from_file_location('assumptions', HERE/'search-assumptions.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


class FilteredMasks:
    def __init__(self, ctx, source, positions):
        self.base = MaskMD5GPU(ctx, source, positions)
        self.ctx = ctx
        kernel = (ROOT/'pair-md5.cl').read_text(encoding='utf8') + '\n' + (HERE/'quoted-mask.cl').read_text(encoding='utf8')
        self.sha256 = hashlib.sha256(kernel.encode()).hexdigest()
        self.program = cl.Program(ctx.context, kernel).build()
        self.kernel = self.program.quoted_masks

    def batch(self, start, size, prefix='3c6'):
        if not 0 <= start < 1 << len(self.base.positions) or not 0 < size <= (1 << len(self.base.positions)) - start:
            raise ValueError('Mask interval outside candidate space')
        capacity = size // 128 + 1024
        mf = cl.mem_flags
        count = np.zeros(1, dtype=np.uint32)
        counter = cl.Buffer(self.ctx.context, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=count)
        mb = cl.Buffer(self.ctx.context, mf.WRITE_ONLY, capacity * 8)
        db = cl.Buffer(self.ctx.context, mf.WRITE_ONLY, capacity * 16)
        self.kernel(self.ctx.queue, (size,), None, self.base.data_buf, np.uint32(self.base.blocks),
                    self.base.prefix_buf, self.base.position_buf, np.uint32(len(self.base.positions)),
                    np.uint64(start), np.uint32(int(prefix, 16)), np.uint32(capacity), counter, mb, db).wait()
        cl.enqueue_copy(self.ctx.queue, count, counter).wait()
        if int(count[0]) > capacity:
            # Never silently drop a survivor if the bounded output buffer fills.
            if size == 1:
                raise RuntimeError('Invalid filter count')
            a, b = self.batch(start, size//2, prefix), self.batch(start+size//2, size-size//2, prefix)
            return sorted(a+b)
        if not count[0]:
            return []
        masks = np.empty(int(count[0]), dtype=np.uint64)
        digests = np.empty((int(count[0]), 4), dtype=np.uint32)
        cl.enqueue_copy(self.ctx.queue, masks, mb).wait()
        cl.enqueue_copy(self.ctx.queue, digests, db).wait()
        return sorted((int(mask), digest.tobytes()) for mask, digest in zip(masks, digests))

    def certify(self):
        comparisons = self.base.certify()
        total = 1 << len(self.base.positions)
        for start, size in [(0,4096), (total//2-2048,4096), (total-4096,4096)]:
            for wanted in ['3c6', hashlib.md5(self.base.witness(start+size//2)).hexdigest()[:3]]:
                expected = [(m, hashlib.md5(self.base.witness(m)).digest()) for m in range(start,start+size)
                            if hashlib.md5(self.base.witness(m)).hexdigest().startswith(wanted)]
                if self.batch(start,size,wanted) != expected:
                    raise RuntimeError('Filtered MD5 survivor set disagrees with hashlib')
                comparisons += size
        return comparisons


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--join', choices=['lf','crlf'], default='lf')
    ap.add_argument('--indices', default='0,1,2,3,4,5,6')
    ap.add_argument('--platform', type=int, default=1)
    ap.add_argument('--batch', type=int, default=1048576)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    indices = [int(x) for x in args.indices.split(',')]
    if not indices or len(set(indices)) != len(indices) or any(i < 0 or i >= 2**31 for i in indices):
        ap.error('Use distinct nonhardened indices')
    if args.batch < 1 or (args.limit is not None and args.limit < 1):
        ap.error('Batch and limit must be positive')
    q = next(x for x in json.loads((ROOT/'aoi-posts-archive.json').read_bytes()) if x['id']=='cleczc')['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0]
    assert hashlib.md5(q.encode()).hexdigest() == '7759227d7406d8230d7e3a8f7b9846d7'
    sep = '\n\n' if args.join == 'lf' else '\r\n\r\n'
    source = sep.join(q.split('\n\n')).encode('ascii')
    boundary, offset = set(), 0
    for p in q.split('\n\n'):
        letters = [i for i,c in enumerate(p) if c.isascii() and c.isalpha()]
        boundary.update([offset+letters[0],offset+letters[-1]])
        if 'post outing himself.' in p:
            boundary.add(offset+p.index('post outing himself.')+len('post outing himself')-1)
        offset += len(p)+len(sep)
    quoted = {i for m in re.finditer(rb'"[^"\r\n]*"',source) for i in [m.start()+1,m.end()-2]}
    positions = sorted(boundary|quoted)
    assert len(boundary)==21 and len(positions)==32
    from bip39_gpu.gpu import context,pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import hash160_to_p2pkh,base58check_encode
    from bip_utils import Bip32Secp256k1,Base58Decoder
    context._global_context=context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback=A.CERT.die_fallback
    md5=FilteredMasks(context._global_context,source,positions)
    comparisons=md5.certify()
    wallet=WalletPathsGPU(context._global_context)
    parent="m/44'/0'/0'/0"
    wallet_comparisons=wallet.certify([{'name':'bip44','parent':parent,'hardened':False,'direct':False}])
    print(f'PASS: {comparisons} MD5/filter comparisons, {wallet_comparisons} independent BIP32 comparisons',flush=True)
    if args.verify_only:
        return
    target=A.TARGETS['example'][0]
    target_hash=Base58Decoder.CheckDecode(target)[1:]
    config={'source_sha256':hashlib.sha256(source).hexdigest(),'join':args.join,'positions':positions,
            'new_quoted_positions':sorted(quoted-boundary),'indices':indices,'md5_prefix':'3c6',
            'target':target,'language':'english','passphrase':'','parent':parent,
            'md5_kernel_sha256':md5.sha256,'wallet_kernel_sha256':wallet.kernel_sha256,
            'gpu_kernel_sha256':A.CERT.gpu_kernel_fingerprint(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'md5_filter_comparisons':comparisons,'bip32_comparisons':wallet_comparisons}
    tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    dest=HERE/f'quoted-masks-{args.join}-{tag}.json'
    total=1<<len(positions)
    state=json.loads(dest.read_bytes()) if dest.exists() else {'configuration':config,'texts_total':total,'next_rank':0,
            'prefix_survivors':0,'derived_addresses':0,'matches':0,'complete':False}
    if state['configuration']!=config:
        raise RuntimeError('Checkpoint configuration differs')
    start=state['next_rank']
    stop=min(total,start+args.limit) if args.limit else total
    begun=time.monotonic();last=begun
    print(f'{dest.name}: {start:,}/{total:,} masks',flush=True)
    while state['next_rank']<stop:
        rank=state['next_rank'];size=min(args.batch,stop-rank)
        rows=md5.batch(rank,size)
        if rows:
            # Every survivor digest is checked with hashlib, not just samples.
            for mask,digest in rows:
                if hashlib.md5(md5.base.witness(mask)).digest()!=digest or not digest.hex().startswith('3c6'):
                    raise RuntimeError('Surviving source bytes fail CPU MD5')
            words=[A.mnemonic(digest) for _,digest in rows]
            seeds=pbkdf2_gpu.pbkdf2_hmac_sha512_gpu([A.HELPER.normalized_password(w) for w in words],[b'mnemonic']*len(words))
            hashes,keys,pubs=wallet.batch(seeds,parent,indices,False,False)
            for k in sorted({0,len(rows)//2,len(rows)-1}):
                seed=hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
                if seed!=seeds[k]:
                    raise RuntimeError('Sample seed differs')
                for j,index in enumerate(indices):
                    node=Bip32Secp256k1.FromSeed(seed).DerivePath(f'{parent}/{index}')
                    pub=node.PublicKey().RawCompressed().ToBytes();r=k*len(indices)+j
                    h=hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest()
                    if hashes[r].tobytes()!=h or keys[r].tobytes()!=node.PrivateKey().Raw().ToBytes() or pubs[r].tobytes()!=pub:
                        raise RuntimeError('Sample key/public/hash160 differs')
            for r in range(len(hashes)):
                if hashes[r].tobytes()!=target_hash:
                    continue
                k,j=divmod(r,len(indices));mask,digest=rows[k]
                seed=hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)
                path=f'{parent}/{indices[j]}'
                node=Bip32Secp256k1.FromSeed(seed).DerivePath(path)
                pub=node.PublicKey().RawCompressed().ToBytes()
                if hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())!=target:
                    raise RuntimeError('Hit failed independent confirmation')
                witness=HERE/f'FOUND-quoted-masks-{args.join}.txt';witness.write_bytes(md5.base.witness(mask))
                A.CERT.atomic_json(witness.with_suffix('.json'),{'address':target,'path':path,'mask':mask,'md5':digest.hex(),
                    'mnemonic':words[k],'private_wif':base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),
                    'configuration':config})
                state['matches']+=1;A.CERT.atomic_json(dest,state)
                print(f'VERIFIED MATCH saved privately at {witness}',flush=True);return
        state['next_rank']+=size
        state['prefix_survivors']+=len(rows)
        state['derived_addresses']+=len(rows)*len(indices)
        state['complete']=state['next_rank']==total
        state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        A.CERT.atomic_json(dest,state)
        now=time.monotonic()
        if now-last>=20 or state['next_rank']==stop:
            print(f"texts={state['next_rank']:,}/{total:,} prefix_survivors={state['prefix_survivors']:,} addresses={state['derived_addresses']:,} elapsed={now-begun:.1f}s",flush=True)
            last=now
    print('COMPLETE, no match' if state['complete'] else 'LIMIT reached; resume the same command',flush=True)


if __name__=='__main__':
    main()
