"""Test documented source variants of the final Quizchain chapter.
Only public source differences are used; no arbitrary spelling dictionary.
Exact original paragraphs + earlier public sections + the verified Finney post.
Deterministic stream, per-buffer MD5 dedup, no prefix filter, checked GPU wallets.
"""
from __future__ import annotations
import argparse, contextlib, datetime, difflib, functools, hashlib, html, importlib.util
import itertools, json, re, sys, time
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PARAS=json.loads((ROOT/'wattpad-paragraphs.json').read_bytes())
GROUPS=[[4,5,6,7],[92,93,94,95],[167,168,169,170],[230,231,232,234]]
TARGETS=['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W','1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']
PARENT="m/44'/0'/0'/0"
MASKS=[15,7,0]+[i for i in range(16) if i not in (15,7,0)]
# (name, joins, internal, NBSP, trailing-space policy)
FORMS=[
 ('draft-lf2','\n\n','\n',' ','keep'),
 ('rendered-lf2','\n\n','\n',' ','trim'),
 ('promoted-lf2','\n\n','\n\n',' ','keep'),
 ('app-lf2','\n\n','\n','\u00a0','keep'),
 ('draft-lf1','\n','\n',' ','keep'),
 ('app-lf1','\n','\n','\u00a0','keep'),
 ('draft-crlf2','\r\n\r\n','\n',' ','keep'),
 ('normalized-crlf2','\r\n\r\n','\r\n',' ','keep'),
]
BASES=[dict(mask=m,start=s,form=f,tail=t) for m in MASKS for s in [0,1,3]
       for f in range(len(FORMS)) for t in ['', '\n']]
BASES=sorted(BASES,key=lambda b:(MASKS.index(b['mask']),b['start'],b['form'],bool(b['tail'])))

class Parser(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.paras=[];self.value=None
 def handle_starttag(self,tag,attrs):
  if tag=='p':
   if self.value is not None:raise ValueError('nested paragraph')
   self.value=[]
  elif tag=='br' and self.value is not None:self.value.append('\n')
 def handle_endtag(self,tag):
  if tag=='p' and self.value is not None:
   self.paras.append(''.join(self.value));self.value=None
 def handle_data(self,data):
  if self.value is not None:self.value.append(data)

@functools.lru_cache(maxsize=None)
def part(id):
 p=Parser();p.feed((ROOT/f'research-2026-09-28/wattpad-parts/{id}.html').read_text(encoding='utf8'))
 return p.paras

def finney():
 text=(ROOT/'hal-finney-page.html').read_text(encoding='latin1')
 text=re.search(r'<div class="post">([\s\S]*?)</div>',text)[1]
 text=re.sub(r'<br\s*/?>\s*<br\s*/?>','\n\n',text,flags=re.I)
 text=re.sub(r'<br\s*/?>','\n',text,flags=re.I)
 return html.unescape(re.sub('<[^>]*>','',text)).strip().split('\n\n')

def norm(s):return re.sub(r'\s+',' ',s).strip()

def build_changes():
 manifest=json.loads((ROOT/'research-2026-09-28/wattpad-parts/manifest.json').read_bytes())['parts']
 changes=[];exact=0
 for id in ['720889517','757574334']:
  old=part(id)
  for i,current in enumerate(PARAS):
   if len(norm(current))<60:continue
   for j,previous in enumerate(old):
    a,b=norm(current),norm(previous)
    if a==b:
     if current!=previous and current.replace('\u00a0',' ' )!=previous.replace('\u00a0',' '):
      changes.append(dict(paragraph=i,replacement=previous,kind='source-whitespace',part=id,source_paragraph=j))
     exact+=1
     continue
    ratio=difflib.SequenceMatcher(None,a,b,autojunk=False).ratio()
    if .5<=len(b)/len(a)<=2 and ratio>=.88:
     changes.append(dict(paragraph=i,replacement=previous,kind='earlier-wording',part=id,source_paragraph=j,ratio=ratio))
 # Match actual forum quote spelling, keeping the chapter's quote delimiters.
 fp=finney()
 assert len(fp)==16 and 'facinating.' in fp[4] and 'fascinating.' in PARAS[233]
 replacement=PARAS[233].replace('fascinating.','facinating.')
 assert replacement==fp[4]
 changes.append(dict(paragraph=233,replacement=replacement,kind='verified-quote-spelling',file='hal-finney-page.html',source_paragraph=4))
 assert len(changes)==10 and len({x['paragraph'] for x in changes})==10,[(x['paragraph'],x['kind']) for x in changes]
 assert sorted(x['paragraph'] for x in changes if x['kind']!='source-whitespace')==[15,18,24,191,193,203,233]
 # Paragraph-specific earlier spellings followed by independent quote delimiters.
 for p,operation in [(230,'opening-quote'),(234,'closing-quote')]:
  replacement=PARAS[p][1:] if p==230 else PARAS[p][:-1]
  assert replacement==(fp[1] if p==230 else fp[5])
  changes.append(dict(paragraph=p,replacement=replacement,kind=operation,file='hal-finney-page.html'))
 return changes

CHANGES=build_changes()
# Whole-section copies address old paragraph boundaries, not just substitutions.
BLOCKS=[
 dict(name='april-second-life',start=10,stop=28,part='720889517',first=0,last=17),
 dict(name='july-thomas-satoshi',start=182,stop=206,part='757574334',first=0,last=len(part('757574334'))),
]
PATTERNS=[]
for mask in range(1,1<<len(CHANGES)):
 PATTERNS.append(dict(kind='local-source-subsets',mask=mask,blocks=()))
# Both complete older sections independently, with/without the actual quote typo.
for bits in range(1,4):
 for quote in [False,True]:
  PATTERNS.append(dict(kind='coherent-earlier-sections',mask=0,blocks=tuple(i for i in [0,1] if bits>>i&1),quote=quote))

def cased(paragraphs,mask):
 out=list(paragraphs)
 for bit,group in enumerate(GROUPS):
  if not mask>>bit&1:continue
  for p in group:
   letters=[i for i,c in enumerate(out[p]) if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz']
   chars=list(out[p]);chars[letters[0]]=chars[letters[0]].lower();chars[letters[-1]]=chars[letters[-1]].upper()
   out[p]=''.join(chars)
 return out

def transform(text,b):
 name,join,internal,nbsp,tails=FORMS[b['form']]
 text=text.replace('\u00a0',nbsp)
 if tails=='trim':text='\n'.join(line.rstrip(' ') for line in text.split('\n'))
 return text.replace('\n',internal).encode('utf8')

@functools.lru_cache(maxsize=2)
def prepared(mask,start,form,tail):
 b=dict(mask=mask,start=start,form=form,tail=tail)
 unchanged=cased(PARAS,mask)
 base=[transform(t,b) for t in unchanged[start:]]
 substitutions=[]
 for change in CHANGES:
  altered=list(PARAS);altered[change['paragraph']]=change['replacement']
  value=cased(altered,mask)[change['paragraph']]
  substitutions.append(transform(value,b))
 return base,substitutions

def materialize(b,pat):
 name,join,internal,nbsp,tails=FORMS[b['form']]
 if not pat['blocks']:
  initial,substitutions=prepared(b['mask'],b['start'],b['form'],b['tail'])
  ps=list(initial)
  for j,change in enumerate(CHANGES):
   if pat['mask']>>j&1:
    ps[change['paragraph']-b['start']]=substitutions[j]
  return join.encode().join(ps)+b['tail'].encode()
 work=list(PARAS)
 if pat.get('quote'):work[233]=PARAS[233].replace('fascinating.','facinating.')
 work=cased(work,b['mask'])
 pieces=[]
 replacements={BLOCKS[k]['start']:BLOCKS[k] for k in pat['blocks']}
 p=b['start']
 while p<len(work):
  if p in replacements:
   block=replacements[p]
   older=part(block['part'])[block['first']:block['last']]
   pieces.extend(transform(t,b) for t in older)
   p=block['stop']
  else:pieces.append(transform(work[p],b));p+=1
 return join.encode().join(pieces)+b['tail'].encode()

def describe(b,pat):
 return dict(base=dict(b,form_name=FORMS[b['form']][0]),
   changes=[{k:v for k,v in c.items() if k!='replacement'} for j,c in enumerate(CHANGES) if pat['mask']>>j&1],
   coherent_blocks=[BLOCKS[k] for k in pat['blocks']],quote_typo=pat.get('quote',False))

def support():
 sys.path.insert(0,str(ROOT/'joint-format-2026-09-28'))
 from checkpoint_io import atomic_json
 spec=importlib.util.spec_from_file_location('source_variant_joint',ROOT/'joint-format-2026-09-28/search.py')
 J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
 return J,atomic_json

def verify():
 for c in CHANGES:
  assert c['replacement']!=PARAS[c['paragraph']]
  if c['kind']=='verified-quote-spelling':
   assert c['replacement']==finney()[4]
 original=materialize(dict(mask=15,start=0,form=0,tail=''),dict(mask=0,blocks=()))
 assert hashlib.sha256(original).hexdigest()=='0648ab3455b4e2812e46ff80d527266bfb5bc8dfbf3850cf66f22115869c4732'
 # Independently reconstruct every variant for a selected draft baseline.
 checked=0
 for mask in range(1,1<<len(CHANGES)):
  ps=list(PARAS)
  for i,c in enumerate(CHANGES):
   if mask>>i&1:ps[c['paragraph']]=c['replacement']
  ps=cased(ps,15)
  expected='\n\n'.join(p.replace('\u00a0',' ') for p in ps).encode()
  got=materialize(dict(mask=15,start=0,form=0,tail=''),dict(mask=mask,blocks=()))
  assert got==expected
  checked+=1
 for block in BLOCKS:
  assert block['stop']>block['start'] and block['last']>block['first']
 return checked

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--indices',default='0,1,2,3,4,5,6')
 ap.add_argument('--platform',type=int,default=1)
 ap.add_argument('--batch',type=int,default=8192)
 ap.add_argument('--limit',type=int)
 ap.add_argument('--verify-only',action='store_true')
 args=ap.parse_args()
 if sys.flags.optimize:ap.error('Python -O disables verification')
 indices=[int(s) for s in args.indices.split(',')]
 if not indices or len(set(indices))!=len(indices) or any(i<0 or i>=2**31 for i in indices):ap.error('Invalid indices')
 if args.batch<1 or args.batch>32768 or (args.limit is not None and args.limit<1):ap.error('Invalid batch/limit')
 checks=verify()
 print(f'PASS: {checks:,} source serialization comparisons; {len(CHANGES)} documented variants; {len(PATTERNS):,} patterns; {len(BASES)} baselines',flush=True)
 if args.verify_only:return
 J,save=support(); wallet=J.Wallet(args.platform,indices)
 from bip_utils import Base58Decoder,Bip32Secp256k1
 from bip39_gpu.gpu.bip32_gpu import base58check_encode,hash160_to_p2pkh
 files=[Path(__file__),ROOT/'wattpad-paragraphs.json',ROOT/'hal-finney-page.html',
   ROOT/'research-2026-09-28/wattpad-parts/720889517.html',ROOT/'research-2026-09-28/wattpad-parts/757574334.html']
 config=dict(family='documented-earlier-source-v1',indices=indices,targets=TARGETS,parent=PARENT,
   language='english',passphrase='',entropy='raw-md5',prefix=None,changes=[{k:v for k,v in x.items() if k!='replacement'}|{'replacement_sha256':hashlib.sha256(x['replacement'].encode()).hexdigest()} for x in CHANGES],
   patterns=PATTERNS,baselines=BASES,files_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
   gpu_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(),wallet_kernel_sha256=wallet.gpu.kernel_sha256)
 config=json.loads(json.dumps(config))  # Canonicalize tuple fields before comparing a loaded checkpoint.
 tag=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
 statepath=HERE/f'source-variants-{tag}.json'
 total=len(BASES)*len(PATTERNS)
 targets={Base58Decoder.CheckDecode(a)[1:]:a for a in TARGETS}
 state=json.loads(statepath.read_bytes()) if statepath.exists() else dict(configuration=config,
  instances_total=total,next_rank=0,unique_entropy_operations=0,derived_addresses=0,matches=[],complete=False,sampled_cpu_comparisons=0,elapsed_search_seconds=0)
 if state['configuration']!=config:raise ValueError('Checkpoint mismatch')
 begun=last=time.monotonic();initial=state['next_rank'];prev_elapsed=state['elapsed_search_seconds']
 stop=min(total,initial+args.limit) if args.limit else total
 print(f'{statepath.name}: {initial:,}/{total:,} candidate instances; per-baseline entropy deduplication; indices={indices}',flush=True)
 compare_start=wallet.comparisons;prev_comp=state['sampled_cpu_comparisons']
 # Dedup within each baseline; on resume reconstruct only this small baseline.
 seen=set();previous_base=-1
 with J.exclusive(statepath.with_suffix('.lock')):
  while state['next_rank']<stop:
   begin_rank=state['next_rank'];rows=[];end=begin_rank
   while end<stop and len(rows)<args.batch:
    bi,pi=divmod(end,len(PATTERNS))
    if bi!=previous_base:
     seen=set();previous_base=bi
     # Previous candidates in this baseline were already checked before restart.
     if end==initial:
      seen={hashlib.md5(materialize(BASES[bi],p)).digest() for p in PATTERNS[:pi]}
    text=materialize(BASES[bi],PATTERNS[pi]);md=hashlib.md5(text).digest()
    if md not in seen:
     seen.add(md);rows.append((md,bi,pi))
    end+=1
   if rows:
    ent=[x[0] for x in rows]
    words,seeds,out=wallet.derive(ent,indices)
    sampled=sorted({0,len(rows)//2,len(rows)-1})
    for k in sampled:
     md,bi,pi=rows[k]
     assert hashlib.md5(materialize(BASES[bi],PATTERNS[pi])).digest()==md
    wallet.compare(words,seeds,out,[(k,ent[k]) for k in sampled],indices)
    for h,address in targets.items():
     for r in wallet.np.flatnonzero(wallet.np.all(out[0]==wallet.np.frombuffer(h,dtype=wallet.np.uint8),axis=1)):
      k,j=divmod(int(r),len(indices));md,bi,pi=rows[k]
      text=materialize(BASES[bi],PATTERNS[pi]);assert hashlib.md5(text).digest()==md
      node=Bip32Secp256k1.FromSeed(hashlib.pbkdf2_hmac('sha512',words[k].encode(),b'mnemonic',2048,64)).DerivePath(f'{PARENT}/{indices[j]}')
      pub=node.PublicKey().RawCompressed().ToBytes()
      assert hash160_to_p2pkh(hashlib.new('ripemd160',hashlib.sha256(pub).digest()).digest())==address
      dest=HERE/f'FOUND-source-variants-{bi}-{pi}-i{indices[j]}.txt';dest.write_bytes(text)
      save(dest.with_suffix('.json'),dict(address=address,path=f'{PARENT}/{indices[j]}',md5=md.hex(),mnemonic=words[k],
       wif=base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),metadata=describe(BASES[bi],PATTERNS[pi])))
      state['matches'].append(dict(address=address,file=dest.name))
      print(f'VERIFIED MATCH saved locally: {dest}',flush=True)
   state['next_rank']=end;state['unique_entropy_operations']+=len(rows);state['derived_addresses']+=len(rows)*len(indices)
   state['sampled_cpu_comparisons']=prev_comp+wallet.comparisons-compare_start
   state['elapsed_search_seconds']=prev_elapsed+time.monotonic()-begun
   state['complete']=end==total;state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
   state['positive_controls']=['stage-one','grycoin-one']
   save(statepath,state)
   now=time.monotonic()
   if now-last>=20 or end==stop or state['matches']:
    speed=(end-initial)/max(now-begun,.001)
    print(f'instances={end:,}/{total:,} entropies={state["unique_entropy_operations"]:,} addresses={state["derived_addresses"]:,} elapsed={now-begun:.1f}s remaining~{(total-end)/speed/60:.1f}min',flush=True);last=now
   if state['matches']:break
 print('VERIFIED MATCH' if state['matches'] else 'COMPLETE, no match in documented-source family' if state['complete'] else 'LIMIT reached; same command resumes',flush=True)

if __name__=='__main__':main()

