"""Compare the failing calibration witness at each derivation stage."""
import hashlib
import json
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dependency',type=Path,default=ROOT/'bip39-gpu-review')
args=parser.parse_args()
sys.path.insert(0,str(args.dependency/'src'))
from bip39_gpu.core.mnemonic import BIP39Mnemonic
from bip39_gpu.gpu import context, pbkdf2_gpu
from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs, hash160_to_p2pkh
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from bip_utils import Bip32Secp256k1
from bip39_gpu.gpu.bip32_gpu import _load_combined_kernel
import numpy as np
import pyopencl as cl

state = json.loads((ROOT/'followup-2026-09-26/example-unfiltered-published-crlf-index0.pre-repair.invalid.json').read_text())
posts = json.loads((ROOT/'aoi-posts-archive.json').read_text())
post = next(x for x in posts if x['id']=='cleczc')
question = post['selftext'].split('Question:\n\n',1)[1].split('\n\nFormat:',1)[0].replace('\n','\r\n')
source = question.encode('ascii')
entropies = []
for rank in [753664,753665,753664+16384,753664+32767]:
    witness = bytearray(source)
    mask = rank ^ (rank >> 1)
    for bit,pos in enumerate(state['offsets']):
        if mask & (1 << bit): witness[pos] ^= 32
    entropies.append(hashlib.md5(witness).digest())
words = [str(BIP39Mnemonic.from_entropy(h)) for h in entropies]
context._global_context = context.GPUContext(platform_id=1)
seeds = pbkdf2_gpu.batch_mnemonic_to_seed_gpu(words)
cpu_seeds = [Bip39SeedGenerator(w).Generate() for w in words]
gpu = batch_seed_to_gpu_outputs(seeds)
cpu_seed_gpu = batch_seed_to_gpu_outputs(cpu_seeds)
for i,h in enumerate(entropies):
    node = Bip44.FromSeed(cpu_seeds[i],Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    print(json.dumps({'entropy':h.hex(),'words':words[i],'seed_match':seeds[i]==cpu_seeds[i],
        'gpu_address':hash160_to_p2pkh(gpu[0][i]),'cpu_seed_gpu_address':hash160_to_p2pkh(cpu_seed_gpu[0][i]),
        'cpu_address':node.PublicKey().ToAddress(),'private_match':gpu[1][i]==node.PrivateKey().Raw().ToBytes(),
        'public_match':gpu[2][i]==node.PublicKey().RawCompressed().ToBytes()}),flush=True)

debug_source = _load_combined_kernel() + '''
__kernel void trace(__global const uchar *seeds, __global uchar *out) {
  uint gid = get_global_id(0);
  uchar seed[64], result[64];
  for(int i=0;i<64;i++) seed[i]=seeds[gid*64+i];
  uchar label[12]={'B','i','t','c','o','i','n',' ','s','e','e','d'};
  hmac_sha512(label,12,seed,64,result);
  uchar key[32], chain[32], next_key[32], next_chain[32];
  uint steps[5]={0x8000002c,0x80000000,0x80000000,0,0};
  for(int step=0;step<6;step++) {
    if(step==0) {
      for(int i=0;i<32;i++) {key[i]=result[i];chain[i]=result[32+i];}
    } else {
      bip32_ckdpriv(key,chain,steps[step-1],next_key,next_chain);
      for(int i=0;i<32;i++) {key[i]=next_key[i];chain[i]=next_chain[i];}
    }
    uint ax[8],ay[8];uchar pub[33];
    secp256k1_point_mul_g(ax,ay,key);secp256k1_pubkey_compressed(pub,ax,ay);
    for(int i=0;i<32;i++) {out[gid*6*97+step*97+i]=key[i];out[gid*6*97+step*97+32+i]=chain[i];}
    for(int i=0;i<33;i++) out[gid*6*97+step*97+64+i]=pub[i];
  }
}
'''
ctx=context._global_context
program=cl.Program(ctx.context,debug_source).build()
data=np.frombuffer(b''.join(cpu_seeds),dtype=np.uint8)
out=np.zeros((len(cpu_seeds),6,97),dtype=np.uint8)
inbuf=cl.Buffer(ctx.context,cl.mem_flags.READ_ONLY|cl.mem_flags.COPY_HOST_PTR,hostbuf=data)
outbuf=cl.Buffer(ctx.context,cl.mem_flags.WRITE_ONLY,out.nbytes)
program.trace(ctx.queue,(len(cpu_seeds),),None,inbuf,outbuf).wait()
cl.enqueue_copy(ctx.queue,out,outbuf).wait()
for i,s in enumerate(cpu_seeds):
    node=Bip32Secp256k1.FromSeed(s)
    for step in range(6):
        if step: node=node.ChildKey([0x8000002c,0x80000000,0x80000000,0,0][step-1])
        print(json.dumps({'candidate':i,'step':step,'key_match':bytes(out[i,step,:32])==node.PrivateKey().Raw().ToBytes(),
            'chain_match':bytes(out[i,step,32:64])==node.ChainCode().ToBytes(),
            'pub_match':bytes(out[i,step,64:])==node.PublicKey().RawCompressed().ToBytes()}))
