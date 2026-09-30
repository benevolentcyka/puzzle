"""Independent nearby paragraph endpoints, motivated by the chapter's 'I STNM'.
The older twist search always couples first+last letters of a nearby paragraph;
this run independently selects its first/last letters. All coherent FFWW group
masks, observed serializer forms, starts and tails. No MD5 prefix filter.
"""
from __future__ import annotations
import argparse,datetime,hashlib,importlib.util,json,random,sys,time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'joint-format-2026-09-28'))
sys.path.insert(0,str(ROOT/'expanded-2026-09-26'))
from checkpoint_io import atomic_json
from mask_md5_gpu import MaskMD5GPU

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
S=module('near_sources',ROOT/'source-variants-2026-09-30/search.py')
NEAR=[3,8,9,91,164,165,166,233]
LETTERS='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

def prepared(b,ends):
 texts=S.cased(S.PARAS,b['mask']);pieces=[];positions=[];labels=[];offset=0
 join=S.FORMS[b['form']][1].encode()
 for p in range(b['start'],len(texts)):
  data=S.transform(texts[p],b)
  if p in NEAR:
   ls=[i for i,c in enumerate(data) if 65<=c<=90 or 97<=c<=122]
   for side,k in [('first',ls[0]),('last',ls[-1])]:
    if ends=='both' or ends==side:positions.append(offset+k);labels.append((p,side))
  pieces.append(data);offset+=len(data)+len(join)
 source=join.join(pieces)+b['tail'].encode()
 assert source==S.materialize(b,dict(mask=0,blocks=()))
 assert positions==sorted(positions) and len(set(positions))==len(positions)
 return source,positions,labels

def reference(b,labels,mask):
 ps=[list(p) for p in S.cased(S.PARAS,b['mask'])]
 for bit,(p,side) in enumerate(labels):
  if mask>>bit&1:
   ls=[i for i,c in enumerate(ps[p]) if c in LETTERS];k=ls[0] if side=='first' else ls[-1]
   ps[p][k]=ps[p][k].swapcase()
 join=S.FORMS[b['form']][1].encode()
 return join.join(S.transform(''.join(p),b) for p in ps[b['start']:])+b['tail'].encode()

def fixture(ends):
 rng=random.Random(777);checked=0
 for bi in sorted({0,1,2,15,31,127,255,511,len(S.BASES)-1}):
  b=S.BASES[bi];source,positions,labels=prepared(b,ends);total=1<<len(positions)
  masks=sorted({0,total-1,*[1<<i for i in range(len(positions))],*[rng.randrange(total) for _ in range(16)]})
  for mask in masks:
   w=bytearray(source)
   for bit,p in enumerate(positions):
    if mask>>bit&1:w[p]^=32
   assert bytes(w)==reference(b,labels,mask)
   checked+=1
 assert len(NEAR)==8 and all(p>=3 for p in NEAR)
 return checked

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--endpoints',choices=['first','last','both'],default='first')
 ap.add_argument('--indices',default='0')
 ap.add_argument('--platform',type=int,default=1)
 ap.add_argument('--batch',type=int,default=16384)
 ap.add_argument('--limit',type=int)
 ap.add_argument('--verify-only',action='store_true')
 args=ap.parse_args()
 if sys.flags.optimize:ap.error('Do not use Python -O')
 indices=[int(i) for i in args.indices.split(',')]
 if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices):ap.error('Use distinct nonhardened indices')
 if not 1<=args.batch<=65536 or (args.limit is not None and args.limit<1):ap.error('Invalid batch/limit')
 checks=fixture(args.endpoints);print(f'PASS: {checks} independent chapter endpoint rebuilds',flush=True)
 if args.verify_only:return
 J=module('near_joint',ROOT/'joint-format-2026-09-28/search.py');wallet=J.Wallet(args.platform,indices)
 from bip_utils import Base58Decoder,Bip32Secp256k1
 from bip39_gpu.gpu.bip32_gpu import base58check_encode,hash160_to_p2pkh
 files=[Path(__file__),ROOT/'source-variants-2026-09-30/search.py',ROOT/'wattpad-paragraphs.json',ROOT/'expanded-2026-09-26/mask_md5_gpu.py',ROOT/'expanded-2026-09-26/mask-md5.cl',ROOT/'pair-md5.cl']
 config=dict(family='independent-nearby-endpoints-v1',near=NEAR,endpoints=args.endpoints,indices=indices,baselines=S.BASES,targets=S.TARGETS,
  raw_md5=True,language='english',passphrase='',parent=S.PARENT,prefix_filter=None,enumeration='baseline-then-binary-endpoint-mask-v1',
  file_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
  crypto_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),wallet_kernel_sha256=wallet.gpu.kernel_sha256)
 config=json.loads(json.dumps(config));tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
 path=HERE/f'near-{args.endpoints}-{tag}.json';per=1<<(16 if args.endpoints=='both' else 8);total=per*len(S.BASES)
 state=json.loads(path.read_bytes()) if path.exists() else dict(configuration=config,next_rank=0,candidates_total=total,derived_addresses=0,matches=[],complete=False,elapsed_search_seconds=0,sampled_cpu_comparisons=0,md5_fixture_checks=0)
 if config!=state['configuration'] or total!=state['candidates_total']:raise ValueError('Checkpoint changed')
 initial=state['next_rank'];stop=min(total,initial+args.limit) if args.limit else total
 start=last=time.monotonic();elapsed=state['elapsed_search_seconds'];comp=wallet.comparisons;old_comp=state['sampled_cpu_comparisons']
 targets={Base58Decoder.CheckDecode(a)[1:]:a for a in S.TARGETS}
 print(f'{path.name}: {initial:,}/{total:,} candidates, indices={indices}',flush=True)
 with J.exclusive(path.with_suffix('.lock')):
  previous=-1;md5=None
  while state['next_rank']<stop:
   rank=state['next_rank'];bi,local=divmod(rank,per);b=S.BASES[bi];size=min(args.batch,per-local,stop-rank)
   if bi!=previous:
    source,positions,labels=prepared(b,args.endpoints);assert len(positions)==(16 if args.endpoints=='both' else 8)
    md5=MaskMD5GPU(wallet.gpu.ctx,source,positions);state['md5_fixture_checks']+=md5.certify();previous=bi
   masks=np.arange(local,local+size,dtype=np.uint64);ent=md5.batch(masks);sample=sorted({0,size//2,size-1})
   for k in sample:
    text=reference(b,labels,int(masks[k]));assert text==md5.witness(masks[k]) and hashlib.md5(text).digest()==ent[k]
   words,seeds,out=wallet.derive(ent,indices);wallet.compare(words,seeds,out,[(k,ent[k]) for k in sample],indices)
   for h,address in targets.items():
    for r in np.flatnonzero(np.all(out[0]==np.frombuffer(h,dtype=np.uint8),axis=1)):
     k,j=divmod(int(r),len(indices));text=reference(b,labels,int(masks[k]));assert hashlib.md5(text).digest()==ent[k]
     node=Bip32Secp256k1.FromSeed(hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)).DerivePath(f'{S.PARENT}/{indices[j]}')
     pub=node.PublicKey().RawCompressed().ToBytes()
     assert hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())==address
     dest=HERE/f'FOUND-near-{rank+k}-i{indices[j]}.txt';dest.write_bytes(text)
     atomic_json(dest.with_suffix('.json'),dict(address=address,base=b,labels=labels,mask=int(masks[k]),md5=ent[k].hex(),mnemonic=words[k],
      private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),path=f'{S.PARENT}/{indices[j]}'))
     state['matches'].append(dict(address=address,file=dest.name));print(f'VERIFIED MATCH saved privately: {dest}',flush=True)
   state['next_rank']+=size;state['derived_addresses']+=size*len(indices);state['complete']=state['next_rank']==total
   state['sampled_cpu_comparisons']=old_comp+wallet.comparisons-comp;state['elapsed_search_seconds']=elapsed+time.monotonic()-start
   state['serializer_fixture_checks']=checks;state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();atomic_json(path,state)
   now=time.monotonic()
   if now-last>=20 or state['next_rank']==stop:
    rate=(state['next_rank']-initial)/max(now-start,.001)
    print(f'candidates={state["next_rank"]:,}/{total:,} addresses={state["derived_addresses"]:,} elapsed={now-start:.1f}s rate={rate:,.0f}/s remaining~{(total-state["next_rank"])/rate/60:.1f}min matches={len(state["matches"])}',flush=True);last=now
   if state['matches']:break
 print('VERIFIED MATCH' if state['matches'] else 'COMPLETE, no match in independent nearby endpoints' if state['complete'] else 'LIMIT reached; same command resumes',flush=True)
if __name__=='__main__':main()
