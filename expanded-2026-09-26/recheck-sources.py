"""Read-only rechecks of primary sources and bounded late-author archive queries."""
import concurrent.futures
import datetime
import gzip
import hashlib
import html
import json
import re
import urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
SOURCES={
    'utxos':'https://mempool.space/api/address/14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W/utxo',
    'outspend':'https://blockstream.info/api/tx/a1916e7ed9eac3fcc56a55056328cb09d06925e2694f2e6720de12b228514d1f/outspend/1',
    'chapter':'https://www.wattpad.com/apiv2/?m=storytext&id=720888559',
    'late_posts':'https://arctic-shift.photon-reddit.com/api/posts/search?author=AoiNakamoto&after=1564963200&limit=100&sort=desc',
    'late_comments':'https://arctic-shift.photon-reddit.com/api/comments/search?author=AoiNakamoto&after=1564963200&limit=100&sort=desc',
    'solver_app':'https://rbbpuzzle.up.railway.app',
    'solver_selftest':'https://rbbpuzzle.up.railway.app/api/selftest',
}


def fetch(item):
    name,url=item
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Quizchain-reproducibility-audit/1.0'})
        with urllib.request.urlopen(request,timeout=25) as response:
            body=response.read(); status=response.status
            wire_bytes=len(body)
            if body.startswith(b'\x1f\x8b'): body=gzip.decompress(body)
        record={'url':url,'http_status':status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
        if wire_bytes!=len(body): record['gzip_wire_bytes']=wire_bytes
        if name=='utxos':
            data=json.loads(body); record['utxos']=data
            record['expected_output_unspent']=any(x['txid']=='a1916e7ed9eac3fcc56a55056328cb09d06925e2694f2e6720de12b228514d1f' and x['vout']==1 and x['value']==77700000 for x in data)
        elif name=='outspend': record['outspend']=json.loads(body)
        elif name.startswith('late_'):
            data=json.loads(body)['data']; record['returned_count']=len(data)
            record['ids']=[x['id'] for x in data]; record['created_utc']=[x['created_utc'] for x in data]
            # A full page would need pagination before any completeness claim.
            record['page_limit_reached']=len(data)==100
        elif name=='chapter':
            text=body.decode('utf8'); paragraphs=[]
            for _,raw in re.findall(r'<p data-p-id="([0-9a-f]+)">(.*?)</p>',text,re.S):
                raw=re.sub(r'<br\s*/?>','\n',raw,flags=re.I)
                paragraphs.append(html.unescape(re.sub(r'<[^>]*>','',raw)))
            expected=json.loads((ROOT/'wattpad-paragraphs.json').read_text(encoding='utf8'))
            record['paragraphs']=len(paragraphs)
            record['paragraph_values_equal_search_source']=paragraphs==expected
            reference=ROOT/'followup-2026-09-26/text/live-720888559.html'
            if reference.exists(): record['body_equal_previous_live_copy']=body==reference.read_bytes()
        elif name=='solver_app':
            text=body.decode('utf8')
            record['script_sources']=re.findall(r'<script[^>]+src=["\']([^"\']+)',text,re.I)
            stage=re.search(r'const STAGE1 = `(.*?)`;',text,re.S)
            if stage: record['hardcoded_stage_one_md5']=hashlib.md5(stage.group(1).replace('\r\n','\n').encode()).hexdigest()
        elif name=='solver_selftest': record['selftest']=json.loads(body)
        return name,record
    except Exception as error:
        return name,{'url':url,'error':str(error),'conclusion':'Unavailable; this failure is not absence evidence.'}


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SOURCES)) as pool:
        records=dict(pool.map(fetch,SOURCES.items()))
    out={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'archive_note':'Late queries cover records returned after 2019-08-05 UTC. They cannot exclude deleted or unarchived material.',
         'sources':records}
    (HERE/'source-recheck.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__': main()
