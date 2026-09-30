"""Check new result receipts, candidate plans and byte-exact Git source blobs."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
result=json.loads((HERE/'results.json').read_bytes())
checked={}
receipts=[]
for record in result['runs']:
    path=ROOT/record['path']
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record['checkpoint_sha256']
    state=json.loads(raw)
    config=state['configuration']
    assert state['next_rank']==record['checked'] and state['candidates_total']==record['total']
    assert state['complete']==record['complete']==(state['next_rank']==state['candidates_total'])
    assert state['derived_addresses']==record['addresses']
    assert len(state['matches'])==record['matches']
    count=state.get('derived_entropies',state['next_rank'])
    assert state['derived_addresses']==count*len(config['indices'])
    if 'derived_entropies' in state:
        assert 0<=count<=state['next_rank']
    for name,wanted in config['source_sha256'].items():
        local=(ROOT/name).resolve()
        local.relative_to(ROOT.resolve())
        assert hashlib.sha256(local.read_bytes()).hexdigest()==wanted,(path.name,name)
        checked[name]=wanted
    if config['family']=='i-stnm-independent-section-layouts-v1':
        plan=HERE/f'chapter-signatures-plan-{path.stem.split("-")[-1]}.json'
        p=json.loads(plan.read_bytes())
        assert p['configuration']==config
        assert p['candidates_total']==state['candidates_total']==sum(b['texts'] for b in p['bases'])
        assert hashlib.sha256(json.dumps(p['bases'],sort_keys=True).encode()).hexdigest()==config['manifest_sha256']
    receipts.append(record['path'])
files=subprocess.run(['git','ls-files','-z'],cwd=ROOT,check=True,capture_output=True).stdout
blobs={}
for raw in files.split(b'\0'):
    if not raw:
        continue
    name=raw.decode()
    if not name.startswith('different-approach-2026-09-30/') or not name.endswith('.py'):
        continue
    indexed=subprocess.run(['git','show',f':{name}'],cwd=ROOT,check=True,capture_output=True).stdout
    assert indexed==(ROOT/name).read_bytes(),f'Git changed runner bytes: {name}'
    blobs[name]=hashlib.sha256(indexed).hexdigest()
assert len(blobs)>=6,'Stage the new Python files before publication verification'
output=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),all_passed=True,
            result_receipts=receipts,checkpoint_bound_sources=checked,byte_exact_git_sources=blobs)
(HERE/'reproducibility-check.json').write_bytes((json.dumps(output,indent=2)+'\n').encode())
print(f'PASS: {len(receipts)} result receipts, {len(checked)} checkpoint-bound sources, {len(blobs)} byte-exact staged sources')
