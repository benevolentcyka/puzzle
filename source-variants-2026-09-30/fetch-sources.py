"""Fetch/verify the two public Wattpad source parts required by the new runners.
HTML stays ignored. Never accept changed source bytes under an old checkpoint.
"""
import argparse,gzip,hashlib,json,os,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT/'research-2026-09-28/wattpad-parts'
IDS=['720889517','757574334']
def verify(data,record,id):
 if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
  raise ValueError(f'{id}: current source does not match the saved manifest; do not reuse old negative checkpoints for changed text')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify-existing',action='store_true');args=ap.parse_args()
 records=json.loads((DEST/'manifest.json').read_bytes())['parts']
 for id in IDS:
  path=DEST/f'{id}.html';record=records[id]
  if path.exists():verify(path.read_bytes(),record,id);print(f'PASS existing {id}: {record["bytes"]:,} bytes');continue
  if args.verify_existing:raise FileNotFoundError(f'Missing {path}; omit --verify-existing to fetch its recorded public URL')
  expected=f'https://www.wattpad.com/apiv2/?m=storytext&id={id}'
  if record['url']!=expected:raise ValueError('Manifest URL differs from the known primary-source endpoint')
  request=urllib.request.Request(expected,headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'gzip'})
  with urllib.request.urlopen(request,timeout=30) as response:
   body=response.read();encoding=response.headers.get('Content-Encoding','').lower()
  data=gzip.decompress(body) if encoding=='gzip' or body[:2]==b'\x1f\x8b' else body
  verify(data,record,id)
  pending=path.with_suffix('.html.tmp')
  with pending.open('wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
  pending.replace(path);print(f'PASS fetched {id}: {len(data):,} bytes')
if __name__=='__main__':main()
