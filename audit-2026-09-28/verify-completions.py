"""Verify saved completion identity without rerunning the exhausted GPU work."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
spec=importlib.util.spec_from_file_location('chapter',ROOT/'expanded-2026-09-26/chapter-subsets.py')
chapter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(chapter)


def main():
    ledger=json.loads((HERE/'verified-expanded-completions.json').read_bytes())
    assert len(ledger['records'])==54
    kernel_sha=chapter.load_cert().gpu_kernel_fingerprint()
    names=set()
    totals={'marked':0,'all-boundaries':0}
    for row in ledger['records']:
        path=ROOT/row['file']
        assert path.name not in names
        names.add(path.name)
        data=path.read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256'],path.name
        state=json.loads(data)
        c=state['configuration']
        scope=c.get('positions_scope','marked')
        low,high=(0,10) if scope=='marked' else (3,3)
        assert (c['minimum_edits'],c['radius'])==(low,high)
        source,positions=chapter.chapter_source(c['join'],c['start_paragraph'],c['spaces'],c['baseline'],c['internal_newlines'],scope)
        assert hashlib.sha256(source).hexdigest()==c['source_sha256']==row['source_sha256']
        assert positions==c['positions'] and c['gpu_kernel_sha256']==kernel_sha
        assert c['indices']==[0] and c['targets']==chapter.TARGETS
        kernel=(ROOT/'pair-md5.cl').read_text(encoding='utf8')+'\n'+(ROOT/'expanded-2026-09-26'/('mask-md5.cl' if scope=='marked' else 'sparse-md5.cl')).read_text(encoding='utf8')
        assert hashlib.sha256(kernel.encode()).hexdigest()==c['md5_kernel_sha256']
        total=sum(math.comb(len(positions),k) for k in range(low,high+1))
        assert state['complete'] and state['matches']==0
        assert state['next_rank']==state['candidates_total']==state['derived_addresses']==row['candidates']==total
        totals[scope]+=total
    assert totals=={'marked':2905043751,'all-boundaries':709943940}
    p=ROOT/'assumptions-2026-09-27/batch-source-spans-example-2de1bff733ef265a.json'
    state=json.loads(p.read_bytes())
    assert state['complete'] and state['matches']==0
    assert state['next_rank']==state['entropy_candidates_total']==27130032
    assert state['derived_addresses']==189910224
    c=state['configuration']
    assert c['prefix_filter'] is None and c['scope']=='bytes' and c['indices']==list(range(7))
    assert c['gpu_kernel_sha256']==kernel_sha
    for name,digest in c['code_sha256'].items():
        assert hashlib.sha256((p.parent/name).read_bytes()).hexdigest()==digest,name
    print('PASS: 54 broad chapter completion records and the completed unfiltered byte-passage search')
    print(json.dumps(totals))


if __name__=='__main__':
    main()
