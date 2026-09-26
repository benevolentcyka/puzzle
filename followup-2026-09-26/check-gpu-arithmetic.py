"""Independently check secp256k1 reduction and full BIP44 GPU derivation."""
import hashlib
import json
import sys
import argparse
from pathlib import Path
import numpy as np
import pyopencl as cl
from bip_utils import Bip32Secp256k1

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dependency',type=Path,default=ROOT/'bip39-gpu-review')
args=parser.parse_args()
sys.path.insert(0,str(args.dependency/'src'))
from bip39_gpu.gpu import context
from bip39_gpu.gpu.bip32_gpu import _load_combined_kernel, batch_seed_to_gpu_outputs

ctx=context.GPUContext(platform_id=1)
context._global_context=ctx
cl_dir=Path(sys.modules['bip39_gpu.gpu.bip32_gpu'].__file__).parent/'cl'
field_source=(cl_dir/'secp256k1.cl').read_text()
field_source+='''
__kernel void reduce_test(__global const uint *data,__global uint *out) {
  uint gid=get_global_id(0);uint r[16],result[8];
  for(int i=0;i<16;i++) r[i]=data[gid*16+i];
  reduce512(r,result);
  for(int i=0;i<8;i++) out[gid*8+i]=result[i];
}
'''
program=cl.Program(ctx.context,field_source).build()
values=[0,1,(1<<256)-1,(1<<512)-1,((1<<256)-1)**2]
for i in range(65536):
    v=int.from_bytes(hashlib.sha512(f'reduction-regression-{i}'.encode()).digest(),'little')
    # Force the high carry that the original kernel dropped.
    if i%2: v=(v&((1<<480)-1))|((0xffffffff-i%512)<<480)
    values.append(v)
data=np.array([[(v>>(32*i))&0xffffffff for i in range(16)] for v in values],dtype=np.uint32)
out=np.zeros((len(values),8),dtype=np.uint32)
ib=cl.Buffer(ctx.context,cl.mem_flags.READ_ONLY|cl.mem_flags.COPY_HOST_PTR,hostbuf=data)
ob=cl.Buffer(ctx.context,cl.mem_flags.WRITE_ONLY,out.nbytes)
program.reduce_test(ctx.queue,(len(values),),None,ib,ob).wait()
cl.enqueue_copy(ctx.queue,out,ob).wait()
p=(1<<256)-(1<<32)-977
for i,v in enumerate(values):
    got=sum(int(x)<<(32*j) for j,x in enumerate(out[i]))
    if got!=v%p: raise RuntimeError(f'Reduction mismatch at vector {i}')
print(f'Reduction: {len(values):,} Python-integer comparisons passed.',flush=True)

seeds=[hashlib.sha512(f'full-bip44-regression-{i}'.encode()).digest() for i in range(8192)]
gpu=batch_seed_to_gpu_outputs(seeds)
for i,s in enumerate(seeds):
    node=Bip32Secp256k1.FromSeed(s).DerivePath("m/44'/0'/0'/0/0")
    key=node.PrivateKey().Raw().ToBytes()
    pub=node.PublicKey().RawCompressed().ToBytes()
    h160=hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest()
    if gpu[0][i]!=h160 or gpu[1][i]!=key or gpu[2][i]!=pub:
        raise RuntimeError(f'Full BIP44 mismatch at vector {i}')
print(f'BIP44: {len(seeds):,} independent key/public-key/hash160 comparisons passed.',flush=True)
result={'reduction_vectors':len(values),'bip44_vectors':len(seeds),'all_passed':True,
        'field_kernel_sha256':hashlib.sha256((cl_dir/'secp256k1.cl').read_bytes()).hexdigest(),
        'device':ctx.device.name,'updated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
(Path(__file__).parent/'gpu-arithmetic-results.json').write_text(json.dumps(result,indent=2)+'\n')
