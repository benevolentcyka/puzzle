"""Independent anomalous capitals with documented block-29 voice/title motifs.
Seven intraword capitals from ppM / VIrgin / BItcoin / BITcoin / AHScoin,
two vOIce pairs, and SECOND title. Optional nearby initials combine the two
publicly motivated clue families. No prefix filter. Both final puzzle targets.
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
S=module('motif_sources',ROOT/'source-variants-2026-09-30/search.py')
ODD=[(72,'ppM',[2]),(127,'VIrgin',[1]),(135,'BItcoin',[1]),(208,'BITcoin',[1,2]),(208,'AHScoin',[1,2])]
NEAR=[3,8,9,91,164,165,166,233]
LETTERS='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
def groups(b,near,mixed_only):
 out=[]
 for p,word,chars in ODD:
  assert S.PARAS[p].count(word)==1
  start=S.PARAS[p].index(word)
  out.extend([[(p,start+k)] for k in chars])
 assert len(out)==7
 if not mixed_only:
  for p in [11,23]:
   assert S.PARAS[p].count('voice')==1;k=S.PARAS[p].index('voice');out.append([(p,k+1),(p,k+2)])
  if b['start']==0:out.append([(0,k) for k in range(1,6)])
 if near:
  for p in NEAR:
   k=next(i for i,c in enumerate(S.PARAS[p]) if c in LETTERS);out.append([(p,k)])
 assert len(set(pair for g in out for pair in g))==sum(map(len,out))
 return out
def prepared(b,g):
 pairs=set(pair for unit in g for pair in unit);offsets={};pieces=[];offset=0;join=S.FORMS[b['form']][1].encode()
 for p,text in enumerate(S.cased(S.PARAS,b['mask'])):
  if p<b['start']:continue
  data=S.transform(text,b)
  want=[i for i,c in enumerate(text) if c in LETTERS];have=[i for i,c in enumerate(data) if 65<=c<=90 or 97<=c<=122]
  assert len(want)==len(have)
  for k,pos in zip(want,have):
   if (p,k) in pairs:offsets[p,k]=offset+pos
  pieces.append(data);offset+=len(data)+len(join)
 source=join.join(pieces)+b['tail'].encode();assert source==S.materialize(b,dict(mask=0,blocks=()))
 positions=sorted(offsets.values());bit={pair:positions.index(pos) for pair,pos in offsets.items()}
 unit_masks=[sum(1<<bit[pair] for pair in unit) for unit in g]
 return source,positions,unit_masks
def reference(b,g,rank):
 ps=[list(p) for p in S.cased(S.PARAS,b['mask'])]
 for bit,unit in enumerate(g):
  if rank>>bit&1:
   for p,k in unit:ps[p][k]=ps[p][k].swapcase()
 return S.FORMS[b['form']][1].encode().join(S.transform(''.join(p),b) for p in ps[b['start']:])+b['tail'].encode()
def mask_table(units):
 result=np.zeros(1<<len(units),dtype=np.uint64);ranks=np.arange(len(result),dtype=np.uint64)
 for bit,mask in enumerate(units):result|=((ranks>>np.uint64(bit))&np.uint64(1))*np.uint64(mask)
 assert len(set(map(int,result)))==len(result)
 return result
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--indices',default='0,1,2,3,4,5,6');ap.add_argument('--near-initials',action='store_true');ap.add_argument('--mixed-only',action='store_true');ap.add_argument('--platform',type=int,default=1);ap.add_argument('--batch',type=int,default=16384);ap.add_argument('--limit',type=int);args=ap.parse_args()
 if sys.flags.optimize:ap.error('Do not use Python -O')
 indices=[int(i) for i in args.indices.split(',')]
 if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices):ap.error('Invalid indices')
 if not 1<=args.batch<=65536 or (args.limit is not None and args.limit<1):ap.error('Invalid batch/limit')
 J=module('motif_joint',ROOT/'joint-format-2026-09-28/search.py');wallet=J.Wallet(args.platform,indices)
 from bip_utils import Base58Decoder,Bip32Secp256k1
 from bip39_gpu.gpu.bip32_gpu import base58check_encode,hash160_to_p2pkh
 files=[Path(__file__),ROOT/'source-variants-2026-09-30/search.py',ROOT/'wattpad-paragraphs.json',ROOT/'expanded-2026-09-26/mask_md5_gpu.py',ROOT/'expanded-2026-09-26/mask-md5.cl',ROOT/'pair-md5.cl']
 config=dict(family='intraword-capital-motifs-v1',odd=ODD,near_initials=args.near_initials,mixed_only=args.mixed_only,baselines=S.BASES,indices=indices,targets=S.TARGETS,language='english',raw_md5=True,passphrase='',parent=S.PARENT,prefix_filter=None,
  file_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},crypto_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),wallet_kernel_sha256=wallet.gpu.kernel_sha256)
 config=json.loads(json.dumps(config));tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16];path=HERE/f'motifs-{tag}.json'
 records=[];total=0
 for b in S.BASES:
  g=groups(b,args.near_initials,args.mixed_only);per=1<<len(g);records.append((b,g,total,total+per));total+=per
 state=json.loads(path.read_bytes()) if path.exists() else dict(configuration=config,next_rank=0,candidates_total=total,derived_addresses=0,matches=[],complete=False,elapsed_search_seconds=0,sampled_cpu_comparisons=0,md5_fixture_checks=0)
 if config!=state['configuration'] or total!=state['candidates_total']:raise ValueError('Checkpoint changed')
 initial=state['next_rank'];stop=min(total,initial+args.limit) if args.limit else total
 start=last=time.monotonic();elapsed=state['elapsed_search_seconds'];comp=wallet.comparisons;old_comp=state['sampled_cpu_comparisons']
 targets={Base58Decoder.CheckDecode(a)[1:]:a for a in S.TARGETS}
 print(f'{path.name}: {initial:,}/{total:,} candidates, indices={indices}',flush=True)
 with J.exclusive(path.with_suffix('.lock')):
  for b,g,first,end in records:
   if end<=state['next_rank'] or first>=stop:continue
   source,positions,units=prepared(b,g);masks=mask_table(units)
   md5=MaskMD5GPU(wallet.gpu.ctx,source,positions);state['md5_fixture_checks']+=md5.certify()
   # Independently check mask order and character locations before any wallet batch.
   for r in sorted({0,len(masks)//2,len(masks)-1,*[1<<i for i in range(len(g))]}):
    assert reference(b,g,r)==md5.witness(masks[r])
    assert int(masks[r])==sum(unit for bit,unit in enumerate(units) if r>>bit&1)
   while state['next_rank']<min(end,stop):
    rank=state['next_rank'];local=rank-first;size=min(args.batch,end-rank,stop-rank);batch=masks[local:local+size]
    ent=md5.batch(batch);sample=sorted({0,size//2,size-1})
    for k in sample:
     text=reference(b,g,local+k);assert text==md5.witness(batch[k]) and hashlib.md5(text).digest()==ent[k]
    words,seeds,out=wallet.derive(ent,indices);wallet.compare(words,seeds,out,[(k,ent[k]) for k in sample],indices)
    for h,address in targets.items():
     for r in np.flatnonzero(np.all(out[0]==np.frombuffer(h,dtype=np.uint8),axis=1)):
      k,j=divmod(int(r),len(indices));text=reference(b,g,local+k);assert hashlib.md5(text).digest()==ent[k]
      node=Bip32Secp256k1.FromSeed(hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)).DerivePath(f'{S.PARENT}/{indices[j]}')
      pub=node.PublicKey().RawCompressed().ToBytes();assert hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())==address
      dest=HERE/f'FOUND-motifs-{rank+k}-i{indices[j]}.txt';dest.write_bytes(text)
      atomic_json(dest.with_suffix('.json'),dict(address=address,base=b,units=g,mask=local+k,md5=ent[k].hex(),mnemonic=words[k],private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),path=f'{S.PARENT}/{indices[j]}'))
      state['matches'].append(dict(address=address,file=dest.name));print(f'VERIFIED MATCH saved privately: {dest}',flush=True)
    state['next_rank']+=size;state['derived_addresses']+=size*len(indices);state['complete']=state['next_rank']==total
    state['sampled_cpu_comparisons']=old_comp+wallet.comparisons-comp;state['elapsed_search_seconds']=elapsed+time.monotonic()-start
    state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();atomic_json(path,state)
    now=time.monotonic()
    if now-last>=20 or state['next_rank']==stop:
     rate=(state['next_rank']-initial)/max(now-start,.001);print(f'candidates={state["next_rank"]:,}/{total:,} addresses={state["derived_addresses"]:,} elapsed={now-start:.1f}s rate={rate:,.0f}/s remaining~{(total-state["next_rank"])/rate/60:.1f}min matches={len(state["matches"])}',flush=True);last=now
    if state['matches']:break
   if state['matches']:break
 print('VERIFIED MATCH' if state['matches'] else 'COMPLETE, no match in capitalization motifs' if state['complete'] else 'LIMIT reached; same command resumes',flush=True)
if __name__=='__main__':main()
