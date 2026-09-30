"""Replay the final uncounted flush of the completed example <=3 case search.
Keep its original result unchanged. Certify lexicographic combinatorial ranks
and check these exact tail candidates against all three public targets.
"""
import datetime,hashlib,importlib.util,itertools,json,math,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'joint-format-2026-09-28'))
from checkpoint_io import atomic_json
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def unrank(n,k,rank):
 if not 0<=rank<math.comb(n,k):raise ValueError('Invalid rank')
 result=[];minimum=0
 for slot in range(k):
  left=k-slot-1
  for v in range(minimum,n-left):
   count=math.comb(n-v-1,left)
   if rank<count:result.append(v);minimum=v+1;break
   rank-=count
 assert rank==0
 return tuple(result)
for n in range(3,10):
 for k in range(1,4):
  assert [unrank(n,k,r) for r in range(math.comb(n,k))]==list(itertools.combinations(range(n),k))
E=module('tail_example',ROOT/'example-crack-2026-09-29/search.py')
original=ROOT/'example-crack-2026-09-29/example-ffww-quad-t3-i0.json'
s=json.loads(original.read_bytes());base=E.baseline_text(E.example_paragraphs(),'ffww-quad');offsets=E.letter_offsets(base);n=len(offsets)
assert s['baseline_md5']==hashlib.md5(base).hexdigest() and s['indices']==[0] and s['complete'] and not s['matches']
assert s['next_rank']==sum(math.comb(n,k) for k in range(4))==s['candidates_total']
first=s['derived'];stop=s['next_rank'];offset=sum(math.comb(n,k) for k in range(3))
assert 0<stop-first<16384 and first>=offset
rows=[]
for rank in range(first,stop):
 combo=tuple(offsets[i] for i in unrank(n,3,rank-offset));text=E.rebuild(base,combo)
 rows.append((rank,combo,hashlib.md5(text).digest()))
assert len(rows)==11130 and rows[-1][1]==tuple(offsets[-3:])
J=module('tail_joint',ROOT/'joint-format-2026-09-28/search.py');wallet=J.Wallet(1,[0])
from bip_utils import Base58Decoder
ent=[r[2] for r in rows];words,seeds,out=wallet.derive(ent,[0]);wallet.compare(words,seeds,out,[(k,ent[k]) for k in [0,len(rows)//2,len(rows)-1]],[0])
matches=[]
for address in [E.EXAMPLE]+E.PRIZES:
 h=wallet.np.frombuffer(Base58Decoder.CheckDecode(address)[1:],dtype=wallet.np.uint8)
 for r in wallet.np.flatnonzero(wallet.np.all(out[0]==h,axis=1)):
  k=int(r);text=E.rebuild(base,rows[k][1]);assert hashlib.md5(text).digest()==ent[k]
  dest=HERE/f'FOUND-example-tail-{rows[k][0]}.txt';dest.write_bytes(text)
  atomic_json(dest.with_suffix('.json'),dict(address=address,rank=rows[k][0],md5=ent[k].hex(),mnemonic=words[k]))
  matches.append(dict(address=address,file=dest.name))
atomic_json(HERE/'example-tail-recheck.json',dict(original_checkpoint=str(original.relative_to(ROOT)).replace('\\','/'),
 original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),baseline_sha256=hashlib.sha256(base).hexdigest(),
 checked_rank_interval=[first,stop],candidates=len(rows),derived_addresses=len(rows),indices=[0],matches=matches,complete=True,
 note='Original runner flushes the final batch, but does not refresh its derived counter. This separate replay closes the counter ambiguity without altering the historical checkpoint.',
 kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
print(f'Rechecked {len(rows):,} final example candidates, matches={len(matches)}',flush=True)
