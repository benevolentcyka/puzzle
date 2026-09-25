"""Build exact byte files for targeted local GPU searches."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
paragraphs=json.loads((here/'wattpad-paragraphs.json').read_text(encoding='utf-8'))
groups=[[4,5,6,7],[92,93,94,95],[167,168,169,170],[230,231,232,234]]

def flip(s):
    c=list(s)
    letters=[i for i,x in enumerate(c) if x.isalpha()]
    if not letters:return s
    c[letters[0]]=c[letters[0]].lower()
    c[letters[-1]]=c[letters[-1]].upper()
    return ''.join(c)

out=here/'bases'
out.mkdir(exist_ok=True)
for name,mask in [('raw',0),('three-groups',7),('four-groups',15)]:
    lines=[]
    for i,s in enumerate(paragraphs):
        if any(mask&(1<<j) and i in g for j,g in enumerate(groups)):
            s=flip(s)
        lines.append(s)
    for sep_name,sep in [('crlfcrlf','\r\n\r\n'),('lflf','\n\n')]:
        b=sep.join(lines).encode('utf-8')
        f=out/f'{name}-{sep_name}.txt'
        f.write_bytes(b)
        n=sum(65<=x<=90 or 97<=x<=122 for x in b)
        print(f'{f.name}: bytes={len(b)} letters={n} pairs={n*(n-1)//2} sha256={hashlib.sha256(b).hexdigest()}')
