"""Verify checkpoint file identities and byte-exact Git publication of new runners."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
result=json.loads((ROOT/'investigation-2026-09-30/results.json').read_bytes())
checked={}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for record in result['runs']:
 path=ROOT/record['path'];s=json.loads(path.read_bytes());c=s['configuration']
 assert digest(path)==record['checkpoint_sha256']
 for key in ['files_sha256','file_sha256']:
  for name,wanted in c.get(key,{}).items():
   p=(ROOT/name).resolve();p.relative_to(ROOT)
   assert digest(p)==wanted,(name,'checkpoint file identity mismatch')
   checked[name]=wanted
 if 'script_sha256' in c:
  name='search-fast.py' if 'fb17a2b64e5cca12' in path.name else 'search.py'
  p=path.parent/name;assert digest(p)==c['script_sha256']
  checked[str(p.relative_to(ROOT)).replace('\\','/')]=digest(p)
 for name,wanted in c.get('bases',{}).items() if isinstance(c.get('bases'),dict) else []:
  assert digest(ROOT/'bases'/name)==wanted
# Confirm that Git stores the same source bytes used by the fingerprinted jobs.
prefixes=['source-variants-2026-09-30/','single-edit-2026-09-30/','near-case-2026-09-30/','case-motifs-2026-09-30/','investigation-2026-09-30/']
listed=subprocess.run(['git','ls-files','-z'],cwd=ROOT,check=True,capture_output=True).stdout
blobs={}
for raw in listed.split(b'\0'):
 if not raw:continue
 name=raw.decode()
 if not any(name.startswith(p) for p in prefixes) or not name.endswith(('.py','.cl')):continue
 actual=(ROOT/name).read_bytes();indexed=subprocess.run(['git','show',f':{name}'],cwd=ROOT,check=True,capture_output=True).stdout
 assert actual==indexed,f'Git normalization changed the recorded source: {name}'
 blobs[name]=hashlib.sha256(indexed).hexdigest()
output=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checkpoint_files=checked,byte_exact_git_sources=blobs,all_passed=True)
(ROOT/'investigation-2026-09-30/reproducibility-check.json').write_bytes((json.dumps(output,indent=2)+'\n').encode())
print(f'PASS: {len(checked)} checkpoint-bound source identities and {len(blobs)} byte-exact staged runner sources')
