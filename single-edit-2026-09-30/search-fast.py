"""Exhaustive one-character copying/editing faults on six final-chapter bases.
A separate, bounded hypothesis: ASCII deletion, adjacent duplication, replacement,
or insertion after coherent FFWW capitalization. Case-only replacements are
excluded since they are already covered. Raw MD5 -> English -> empty passphrase
-> BIP44, both public prize addresses. GPU MD5 is independently certified.
"""
from __future__ import annotations
import argparse, datetime, hashlib, importlib.util, json, random, struct, sys, time
from pathlib import Path
import numpy as np
import pyopencl as cl

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'joint-format-2026-09-28'))
from checkpoint_io import atomic_json
ALPHABET=bytes([9,10,13]+list(range(32,127)))
KINDS=['delete','duplicate','replace','insert']
FILES=[
 'four-groups-lflf-nbsp-space.txt','three-groups-lflf-nbsp-space.txt',
 'four-groups-lflf-rendered.txt','three-groups-lflf-rendered.txt',
 'four-groups-crlfjoin-nbsp-space.txt','three-groups-crlfjoin-nbsp-space.txt',
]
TARGETS=['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W','1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']
PARENT="m/44'/0'/0'/0"

def witness(source,edit):
 p,k,c=map(int,edit)
 return source[:p]+source[p+1:] if k==0 else source[:p]+bytes([c])+source[p:] if k==1 else source[:p]+bytes([c])+source[p+1:]

class GPU:
 def __init__(self,ctx,program,source):
  self.ctx,self.program,self.source=ctx,program,source
  padded=source+b'\x80';padded+=b'\0'*((56-len(padded)%64)%64);padded+=struct.pack('<Q',len(source)*8)
  mf=cl.mem_flags
  self.raw=cl.Buffer(ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=np.frombuffer(padded,dtype=np.uint32))
  self.prefix=cl.Buffer(ctx.context,mf.READ_WRITE,(len(padded)//64+1)*16)
  cl.Kernel(program,'md5_prefix')(ctx.queue,(1,),None,self.raw,np.uint32(len(padded)//64),self.prefix).wait()
  self.kernel=cl.Kernel(program,'md5_single_edit')
 def batch(self,edits):
  edits=np.asarray(edits,dtype=np.uint32).reshape((-1,3))
  if not len(edits):return []
  assert np.all(edits[:,0]<=len(self.source)) and np.all(edits[:,1]<=2) and np.all(edits[:,2]<=255)
  assert not np.any((edits[:,1]!=1)&(edits[:,0]==len(self.source)))
  out=np.empty((len(edits),4),dtype=np.uint32);mf=cl.mem_flags
  eb=cl.Buffer(self.ctx.context,mf.READ_ONLY|mf.COPY_HOST_PTR,hostbuf=edits)
  ob=cl.Buffer(self.ctx.context,mf.WRITE_ONLY,out.nbytes)
  self.kernel(self.ctx.queue,(len(edits),),None,self.raw,np.uint32(len(self.source)),self.prefix,eb,ob).wait()
  cl.enqueue_copy(self.ctx.queue,out,ob).wait()
  return [row.tobytes() for row in out]
 def certify(self,edits):
  got=self.batch(edits)
  for edit,md in zip(edits,got):
   assert md==hashlib.md5(witness(self.source,edit)).digest(),f'GPU MD5 mismatch at {tuple(edit)}'
  return len(got)

class Space:
 def __init__(self,source,kind):
  self.source,self.kind=source,kind
  self.positions=np.asarray([i for i,c in enumerate(source) if c<128],dtype=np.uint32)
  if kind=='insert':
   self.positions=np.asarray([i for i,c in enumerate(source) if c&192!=128]+[len(source)],dtype=np.uint32)
   self.total=len(self.positions)*len(ALPHABET)
  elif kind=='replace':
   # Keep the space finite and omit unchanged or already-covered case-only edits.
   self.allowed={old:bytes(c for c in ALPHABET if c!=old and not ((65<=old<=90 or 97<=old<=122) and c==old^32)) for old in set(source) if old<128}
   self.counts=np.asarray([len(self.allowed[source[int(p)]]) for p in self.positions],dtype=np.uint64)
   self.ends=np.cumsum(self.counts);self.total=int(self.ends[-1])
  else:self.total=len(self.positions)
 def descriptor(self,rank):
  if not 0<=rank<self.total:raise ValueError('Rank outside the edit space')
  if self.kind=='insert':
   a,b=divmod(rank,len(ALPHABET));return int(self.positions[a]),1,ALPHABET[b]
  if self.kind=='replace':
   a=int(np.searchsorted(self.ends,rank,side='right'));b=rank-(int(self.ends[a-1]) if a else 0)
   p=int(self.positions[a]);return p,2,self.allowed[self.source[p]][b]
  p=int(self.positions[rank]);return p,0 if self.kind=='delete' else 1,0 if self.kind=='delete' else self.source[p]
 def batch(self,start,size):
  ranks=np.arange(start,start+size,dtype=np.uint64)
  if self.kind in ['delete','duplicate']:
   ps=self.positions[start:start+size]
   cs=np.zeros(size,dtype=np.uint32) if self.kind=='delete' else np.frombuffer(self.source,dtype=np.uint8)[ps].astype(np.uint32)
   return np.column_stack([ps,np.full(size,0 if self.kind=='delete' else 1,dtype=np.uint32),cs]).astype(np.uint32)
  if self.kind=='insert':
   ps=self.positions[ranks//len(ALPHABET)]
   cs=np.frombuffer(ALPHABET,dtype=np.uint8)[ranks%len(ALPHABET)]
   return np.column_stack([ps,np.full(size,1,dtype=np.uint32),cs]).astype(np.uint32)
  at=np.searchsorted(self.ends,ranks,side='right')
  before=np.where(at>0,self.ends[np.maximum(at-1,0)],0)
  ps=self.positions[at];old=np.frombuffer(self.source,dtype=np.uint8)[ps]
  table=np.zeros((128,len(ALPHABET)),dtype=np.uint32)
  for c,allowed in self.allowed.items():table[c,:len(allowed)]=np.frombuffer(allowed,dtype=np.uint8)
  cs=table[old,ranks-before]
  return np.column_stack([ps,np.full(size,2,dtype=np.uint32),cs]).astype(np.uint32)

def support():
 spec=importlib.util.spec_from_file_location('single_joint',ROOT/'joint-format-2026-09-28/search.py')
 J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
 return J

def certify(program,ctx):
 rng=random.Random(777);checks=0
 for length in [0,1,2,3,55,56,57,63,64,65,119,120,121,127,128,129,255,256,257]:
  source=bytes(rng.randrange(256) for _ in range(length));edits=[]
  for p in sorted({0,length,length//2,*[z for z in [54,55,56,63,64,119,120,127,128] if z<=length]}):
   for c in [0,9,10,13,32,65,127,128,194,255]:
    edits.append((p,1,c))
    if p<length:edits.extend([(p,0,0),(p,2,c)])
  gpu=GPU(ctx,program,source);checks+=gpu.certify(edits)
 # Enumeration is independently compared to straightforward position/alphabet loops.
 for source in [b'Aa! \n',b'a\xc2\xa0b\r\n']:
  for kind in KINDS:
   space=Space(source,kind)
   if kind=='insert':expected=[(p,1,c) for p in range(len(source)+1) if p==len(source) or source[p]&192!=128 for c in ALPHABET]
   elif kind=='replace':expected=[(p,2,c) for p,old in enumerate(source) if old<128 for c in ALPHABET if c!=old and not (chr(old).isascii() and chr(old).isalpha() and c==old^32)]
   else:expected=[(p,0 if kind=='delete' else 1,0 if kind=='delete' else old) for p,old in enumerate(source) if old<128]
   assert space.total==len(expected)
   actual=[tuple(map(int,e)) for e in space.batch(0,space.total)]
   assert actual==expected
   gpu=GPU(ctx,program,source);checks+=gpu.certify(expected)
 for name in [FILES[0],FILES[4]]:
  source=(ROOT/'bases'/name).read_bytes();assert all(c<128 for c in source)
  edits=[(rng.randrange(len(source)+1) if k==1 else rng.randrange(len(source)),k,rng.randrange(256)) for k in [0,1,2] for _ in range(341)]
  edits.append((len(source),1,32))
  checks+=GPU(ctx,program,source).certify(edits)
 return checks

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--family',choices=KINDS+['small','all'],default='small')
 ap.add_argument('--bases',choices=['draft','calibrated'],default='calibrated')
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
 J=support();wallet=J.Wallet(args.platform,indices)
 from bip_utils import Base58Decoder,Bip32Secp256k1
 from bip39_gpu.gpu.bip32_gpu import hash160_to_p2pkh,base58check_encode
 kernel=(ROOT/'pair-md5.cl').read_text(encoding='utf8')+'\n'+(HERE/'fast-edit.cl').read_text(encoding='utf8')
 program=cl.Program(wallet.gpu.ctx.context,kernel).build()
 checks=certify(program,wallet.gpu.ctx)
 print(f'PASS: {checks:,} independent variable-length GPU MD5 checks and edit enumeration checks; solved wallet controls passed',flush=True)
 if args.verify_only:return
 files=FILES[:2] if args.bases=='draft' else FILES
 families=KINDS[:2] if args.family=='small' else KINDS if args.family=='all' else [args.family]
 config=dict(family='single-ascii-edit-v1',families=families,bases={p:hashlib.sha256((ROOT/'bases'/p).read_bytes()).hexdigest() for p in files},
  alphabet_hex=ALPHABET.hex(),indices=indices,targets=TARGETS,parent=PARENT,entropy='raw-md5',language='english',passphrase='',
  excluded='identity substitutions and substitutions that only change case',prefix_filter=None,
  gpu_md5_kernel_sha256=hashlib.sha256(kernel.encode()).hexdigest(),wallet_kernel_sha256=wallet.gpu.kernel_sha256,
  crypto_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
 path=HERE/f'one-edit-{args.family}-{args.bases}-{tag}.json'
 records=[];total=0
 for kind in families:
  for name in files:
   source=(ROOT/'bases'/name).read_bytes();space=Space(source,kind)
   records.append((name,source,space,total,total+space.total));total+=space.total
 state=json.loads(path.read_bytes()) if path.exists() else dict(configuration=config,next_rank=0,candidates_total=total,
  derived_addresses=0,matches=[],complete=False,elapsed_search_seconds=0,sampled_cpu_comparisons=0)
 if state['configuration']!=config or state['candidates_total']!=total:raise ValueError('Checkpoint mismatch')
 stop=min(total,state['next_rank']+args.limit) if args.limit else total
 initial=state['next_rank'];begun=last=time.monotonic();elapsed=state['elapsed_search_seconds']
 sample_start=wallet.comparisons;prev_comp=state['sampled_cpu_comparisons']
 targets={Base58Decoder.CheckDecode(a)[1:]:a for a in TARGETS}
 print(f'{path.name}: {initial:,}/{total:,} candidates, {total*len(indices):,} address operations, indices={indices}',flush=True)
 with J.exclusive(path.with_suffix('.lock')):
  for name,source,space,first,end in records:
   if end<=state['next_rank'] or first>=stop:continue
   gpu=GPU(wallet.gpu.ctx,program,source)
   probes=[]
   for r in sorted({0,space.total//2,space.total-1,*[rng%space.total for rng in [63,64,55,56,57,127,128,255,4096]]}):
    probes.append(tuple(map(int,space.batch(r,1)[0])))
   gpu.certify(probes)
   while state['next_rank']<min(end,stop):
    rank=state['next_rank'];local=rank-first;size=min(args.batch,end-rank,stop-rank)
    edits=space.batch(local,size);ent=gpu.batch(edits)
    sample=sorted({0,size//2,size-1})
    for k in sample:assert ent[k]==hashlib.md5(witness(source,edits[k])).digest()
    words,seeds,out=wallet.derive(ent,indices);wallet.compare(words,seeds,out,[(k,ent[k]) for k in sample],indices)
    for h,address in targets.items():
     for r in wallet.np.flatnonzero(wallet.np.all(out[0]==wallet.np.frombuffer(h,dtype=np.uint8),axis=1)):
      k,j=divmod(int(r),len(indices));text=witness(source,edits[k]);assert hashlib.md5(text).digest()==ent[k]
      node=Bip32Secp256k1.FromSeed(hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)).DerivePath(f'{PARENT}/{indices[j]}')
      pub=node.PublicKey().RawCompressed().ToBytes()
      assert hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())==address
      dest=HERE/f'FOUND-one-edit-{rank+k}-i{indices[j]}.txt';dest.write_bytes(text)
      atomic_json(dest.with_suffix('.json'),dict(address=address,md5=ent[k].hex(),mnemonic=words[k],private_wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),
       base=name,edit=list(map(int,edits[k])),path=f'{PARENT}/{indices[j]}'))
      state['matches'].append(dict(address=address,file=dest.name))
      print(f'VERIFIED MATCH saved privately: {dest}',flush=True)
    state['next_rank']+=size;state['derived_addresses']+=size*len(indices);state['complete']=state['next_rank']==total
    state['elapsed_search_seconds']=elapsed+time.monotonic()-begun;state['sampled_cpu_comparisons']=prev_comp+wallet.comparisons-sample_start
    state['md5_fixture_checks']=checks;state['positive_controls']=['stage-one','grycoin-one']
    state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();atomic_json(path,state)
    now=time.monotonic()
    if now-last>=20 or state['next_rank']==stop or state['matches']:
     speed=(state['next_rank']-initial)/max(now-begun,.001)
     print(f'candidates={state["next_rank"]:,}/{total:,} addresses={state["derived_addresses"]:,} rate={speed:,.0f}/s elapsed={now-begun:.1f}s remaining~{(total-state["next_rank"])/speed/60:.1f}min matches={len(state["matches"])}',flush=True);last=now
    if state['matches']:break
   if state['matches']:break
 print('VERIFIED MATCH' if state['matches'] else 'COMPLETE, no match in bounded one-edit family' if state['complete'] else 'LIMIT reached; same command resumes',flush=True)
if __name__=='__main__':main()

