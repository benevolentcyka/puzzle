"""Cached-parent generic BIP32 path derivation, certified using bip_utils."""
import hashlib
from pathlib import Path
import numpy as np
import pyopencl as cl
from bip39_gpu.gpu.bip32_gpu import _load_combined_kernel

HERE = Path(__file__).resolve().parent


def parse_path(path):
    pieces = path.split('/')
    if pieces[0] != 'm': raise ValueError('Path must start with m')
    result = []
    for p in pieces[1:]:
        hardened = p.endswith("'")
        value = int(p[:-1] if hardened else p)
        if not 0 <= value < 2**31: raise ValueError('Invalid child index')
        result.append(value | (0x80000000 if hardened else 0))
    return result


def full_path(parent, index, hardened=False, direct=False):
    return parent if direct else parent + '/' + str(index) + ("'" if hardened else '')


class WalletPathsGPU:
    def __init__(self, ctx):
        self.ctx = ctx
        primitives = _load_combined_kernel()
        if primitives is None: raise RuntimeError('Missing GPU primitive source')
        source = primitives + '\n' + (HERE/'wallet-paths.cl').read_text(encoding='utf8')
        self.kernel_sha256 = hashlib.sha256(source.encode()).hexdigest()
        self.program = cl.Program(ctx.context, source).build()
        self.parents_kernel = self.program.wallet_parents
        self.children_kernel = self.program.wallet_children

    def batch(self, seeds, parent, indices, hardened=False, direct=False):
        if not seeds or not indices or any(len(s)!=64 for s in seeds): raise ValueError('Use nonempty 64-byte seeds and indices')
        if direct and len(indices) != 1: raise ValueError('A direct node has one address')
        path = parse_path(parent)
        values = [i | (0x80000000 if hardened else 0) for i in indices]
        if any(i < 0 or i >= 2**31 for i in indices): raise ValueError('Use nonnegative indices below 2**31')
        mf = cl.mem_flags
        sb = cl.Buffer(self.ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=np.frombuffer(b''.join(seeds),dtype=np.uint8))
        pb = cl.Buffer(self.ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=np.asarray(path or [0],dtype=np.uint32))
        ib = cl.Buffer(self.ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=np.asarray(values,dtype=np.uint32))
        parents = cl.Buffer(self.ctx.context,mf.READ_WRITE,len(seeds)*64)
        self.parents_kernel(self.ctx.queue,(len(seeds),),None,sb,pb,np.uint32(len(path)),parents).wait()
        count = len(seeds)*len(indices)
        hashes = np.empty((count,20),dtype=np.uint8)
        keys = np.empty((count,32),dtype=np.uint8)
        pubs = np.empty((count,33),dtype=np.uint8)
        hb = cl.Buffer(self.ctx.context,mf.WRITE_ONLY,hashes.nbytes)
        kb = cl.Buffer(self.ctx.context,mf.WRITE_ONLY,keys.nbytes)
        ub = cl.Buffer(self.ctx.context,mf.WRITE_ONLY,pubs.nbytes)
        self.children_kernel(self.ctx.queue,(count,),None,parents,ib,np.uint32(len(indices)),np.uint32(direct),hb,kb,ub).wait()
        for host,device in [(hashes,hb),(keys,kb),(pubs,ub)]: cl.enqueue_copy(self.ctx.queue,host,device).wait()
        return hashes,keys,pubs

    def certify(self, presets):
        from bip_utils import Bip32Secp256k1
        seeds = [hashlib.sha512(f'wallet-path-vector-{i}'.encode()).digest() for i in range(12)]
        compared = 0
        for preset in presets:
            indices = [0] if preset['direct'] else [0,1,20,0x7fffffff]
            hashes,keys,pubs = self.batch(seeds,preset['parent'],indices,preset['hardened'],preset['direct'])
            for row,seed in enumerate(seeds):
                for j,index in enumerate(indices):
                    node = Bip32Secp256k1.FromSeed(seed).DerivePath(full_path(preset['parent'],index,preset['hardened'],preset['direct']))
                    k = row*len(indices)+j
                    public = node.PublicKey().RawCompressed().ToBytes()
                    hash160 = hashlib.new('ripemd160',hashlib.sha256(public).digest()).digest()
                    if keys[k].tobytes()!=node.PrivateKey().Raw().ToBytes() or pubs[k].tobytes()!=public or hashes[k].tobytes()!=hash160:
                        raise RuntimeError(f'Independent generic BIP32 mismatch at {preset["name"]}, seed {row}, index {index}')
                    compared += 1
        return compared
