"""Every subset of the 16 marked FFWW paragraphs, changing both endpoints together.
This is not a coherent whole-group subset: each marked paragraph is independent.
48 chapter serializer/start/tail forms; no prefix filter; both prize targets.
"""
from __future__ import annotations
import argparse,datetime,hashlib,importlib.util,json,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'joint-format-2026-09-28'));sys.path.insert(0,str(ROOT/'expanded-2026-09-26'))
from checkpoint_io import atomic_json
from mask_md5_gpu import MaskMD5GPU
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
S=module('paired_sources',ROOT/'source-variants-2026-09-30/search.py')
MARKED=sorted(p for g in S.GROUPS for p in g)
BASES=[b for b in S.BASES if b['mask']==15]
assert len(BASES)==48 and len(MARKED)==16
def prepared(b):
 pieces=[];positions=[];offset=0;join=S.FORMS[b['form']][1].encode()
 for p,text in enumerate(S.cased(S.PARAS,15)):
  if p<b['start']:continue
  data=S.transform(text,b)
  if p in MARKED:
   ls=[i for i,c in enumerate(data) if 65<=c<=90 or 97<=c<=122];positions.extend([offset+ls[0],offset+ls[-1]])
  pieces.append(data);offset+=len(data)+len(join)
 source=join.join(pieces)+b['tail'].encode()
 assert source==S.materialize(b,dict(mask=0,blocks=())) and len(positions)==32
 return source,positions
def masks_for(start,size):
 ranks=np.arange(start,start+size,dtype=np.uint64);masks=np.zeros(size,dtype=np.uint64)
 for bit in range(16):masks|=((ranks>>np.uint64(bit))&np.uint64(1))<<np.uint64(2*bit);masks|=((ranks>>np.uint64(bit))&np.uint64(1))<<np.uint64(2*bit+1)
 return masks
def reference(b,rank):
 ps=[list(p) for p in S.cased(S.PARAS,15)]
 for bit,p in enumerate(MARKED):
  if rank>>bit&1:
   ls=[i for i,c in enumerate(ps[p]) if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz']
   for k in [ls[0],ls[-1]]:ps[p][k]=ps[p][k].swapcase()
 return S.FORMS[b['form']][1].encode().join(S.transform(''.join(p),b) for p in ps[b['start']:])+b['tail'].encode()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--indices',default='0,1,2,3,4,5,6');ap.add_argument('--platform',type=int,default=1);ap.add_argument('--batch',type=int,default=16384);ap.add_argument('--limit',type=int);args=ap.parse_args()
 if sys.flags.optimize:ap.error('Do not use Python -O')
 indices=[int(i) for i in args.indices.split(',')]
 if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices):ap.error('Invalid indices')
 if not 1<=args.batch<=65536 or (args.limit is not None and args.limit<1):ap.error('Invalid batch/limit')
 # Check the whole rank-to-mask mapping against independent Python bit construction.
 actual=masks_for(0,1<<16)
 assert [int(m) for m in actual]==[sum(3<<(2*k) for k in range(16) if r>>k&1) for r in range(1<<16)]
 print('PASS: 65,536 independent paired-mask enumerations',flush=True)
 J=module('paired_joint',ROOT/'joint-format-2026-09-28/search.py');wallet=J.Wallet(args.platform,indices)
 from bip_utils import Base58Decoder,Bip32Secp256k1
 from bip39_gpu.gpu.bip32_gpu import base58check_encode,hash160_to_p2pkh
 files=[Path(__file__),ROOT/'source-variants-2026-09-30/search.py',ROOT/'wattpad-paragraphs.json',ROOT/'expanded-2026-09-26/mask_md5_gpu.py',ROOT/'expanded-2026-09-26/mask-md5.cl',ROOT/'pair-md5.cl']
 config=dict(family='independent-marked-paragraph-pairs-v1',marked=MARKED,baselines=BASES,indices=indices,targets=S.TARGETS,language='english',raw_md5=True,passphrase='',parent=S.PARENT,prefix_filter=None,
  file_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},crypto_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),wallet_kernel_sha256=wallet.gpu.kernel_sha256)
 config=json.loads(json.dumps(config));tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
 path=HERE/f'paired-{tag}.json';per=1<<16;total=per*len(BASES)
 state=json.loads(path.read_bytes()) if path.exists() else dict(configuration=config,next_rank=0,candidates_total=total,derived_addresses=0,matches=[],complete=False,elapsed_search_seconds=0,sampled_cpu_comparisons=0,md5_fixture_checks=0)
 if config!=state['configuration'] or total!=state['candidates_total']:raise ValueError('Checkpoint changed')
 initial=state['next_rank'];stop=min(total,initial+args.limit) if args.limit else total
 start=last=time.monotonic();elapsed=state['elapsed_search_seconds'];comp=wallet.comparisons;old_comp=state['sampled_cpu_comparisons']
 targets={Base58Decoder.CheckDecode(a)[1:]:a for a in S.TARGETS}
 print(f'{path.name}: {initial:,}/{total:,} candidates, indices={indices}',flush=True)
 with J.exclusive(path.with_suffix('.lock')):
  previous=-1;md5=None
  while state['next_rank']<stop:
   rank=state['next_rank'];bi,local=divmod(rank,per);b=BASES[bi];size=min(args.batch,per-local,stop-rank)
   if bi!=previous:
    source,positions=prepared(b);md5=MaskMD5GPU(wallet.gpu.ctx,source,positions);state['md5_fixture_checks']+=md5.certify();previous=bi
   masks=masks_for(local,size);ent=md5.batch(masks);sample=sorted({0,size//2,size-1})
   for k in sample:
    text=reference(b,local+k);assert text==md5.witness(masks[k]) and hashlib.md5(text).digest()==ent[k]
   words,seeds,out=wallet.derive(ent,indices);wallet.compare(words,seeds,out,[(k,ent[k]) for k in sample],indices)
   for h,address in targets.items():
    for r in np.flatnonzero(np.all(out[0]==np.frombuffer(h,dtype=np.uint8),axis=1)):
     k,j=divmod(int(r),len(indices));text=reference(b,local+k);assert hashlib.md5(text).digest()==ent[k]
     node=Bip32Secp256k1.FromSeed(hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)).DerivePath(f'{S.PARENT}/{indices[j]}')
     pub=node.PublicKey().RawCompressed().ToBytes();assert hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())==address
     dest=HERE/f'FOUND-paired-{rank+k}-i{indices[j]}.txt';dest.write_bytes(text)
     atomic_json(dest.with_suffix('.json'),dict(address=address,base=b,omitted_marked_paragraph_mask=local+k,md5=ent[k].hex(),mnemonic=words[k],private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),path=f'{S.PARENT}/{indices[j]}'))
     state['matches'].append(dict(address=address,file=dest.name));print(f'VERIFIED MATCH saved privately: {dest}',flush=True)
   state['next_rank']+=size;state['derived_addresses']+=size*len(indices);state['complete']=state['next_rank']==total
   state['sampled_cpu_comparisons']=old_comp+wallet.comparisons-comp;state['elapsed_search_seconds']=elapsed+time.monotonic()-start
   state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();atomic_json(path,state)
   now=time.monotonic()
   if now-last>=20 or state['next_rank']==stop:
    rate=(state['next_rank']-initial)/max(now-start,.001);print(f'candidates={state["next_rank"]:,}/{total:,} addresses={state["derived_addresses"]:,} elapsed={now-start:.1f}s rate={rate:,.0f}/s remaining~{(total-state["next_rank"])/rate/60:.1f}min matches={len(state["matches"])}',flush=True);last=now
   if state['matches']:break
 print('VERIFIED MATCH' if state['matches'] else 'COMPLETE, no match in independent marked paragraph pairs' if state['complete'] else 'LIMIT reached; same command resumes',flush=True)
if __name__=='__main__':main()
