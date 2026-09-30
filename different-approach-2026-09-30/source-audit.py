"""Compare the chapter with all captured author sources; do not guess edits."""
import datetime
import difflib
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paragraphs, self.current = [], None

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            if self.current is not None:
                raise ValueError('Nested paragraph')
            self.current = []
        elif tag == 'br' and self.current is not None:
            self.current.append('\n')

    def handle_endtag(self, tag):
        if tag == 'p' and self.current is not None:
            self.paragraphs.append(''.join(self.current))
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)


def normalized(s):
    return re.sub(r'\s+', ' ', s).strip()


def main():
    chapter = json.loads((ROOT / 'wattpad-paragraphs.json').read_bytes())
    manifest = json.loads((ROOT / 'research-2026-09-28/wattpad-parts/manifest.json').read_bytes())
    corpus = []
    sources = []
    for part_id, record in manifest['parts'].items():
        path = ROOT / f'research-2026-09-28/wattpad-parts/{part_id}.html'
        raw = path.read_bytes()
        if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise RuntimeError(f'Source fingerprint mismatch: {path}')
        parser = Paragraphs()
        parser.feed(raw.decode('utf8'))
        if part_id == '720888559':
            assert parser.paragraphs == chapter
            continue
        sources.append(dict(id=part_id, kind='wattpad', **record))
        for i, text in enumerate(parser.paragraphs):
            corpus.append((text, dict(kind='wattpad', id=part_id, title=record['title'],
                                     paragraph=i, url=record['url'], modify_date=record['modifyDate'])))
    for file, field in [('aoi-posts-archive.json', 'selftext'), ('aoi-comments-archive.json', 'body')]:
        raw = (ROOT / file).read_bytes()
        records = json.loads(raw)
        sources.append(dict(file=file, records=len(records), sha256=hashlib.sha256(raw).hexdigest()))
        for record in records:
            text = record.get(field, '')
            for i, paragraph in enumerate(text.split('\n\n')):
                corpus.append((paragraph, dict(kind='reddit', id=record['id'], field=field,
                                               paragraph=i, created_utc=record['created_utc'],
                                               url='https://www.reddit.com' + record.get('permalink', ''))))
    # Exact body duplicates across reposts need one comparison, retaining provenance.
    unique = {}
    for text, label in corpus:
        norm = normalized(text)
        if len(norm) >= 60:
            entry = unique.setdefault(norm, dict(text=text, sources=[]))
            entry['sources'].append(label)
    changes, exact = [], []
    for p, current in enumerate(chapter):
        a = normalized(current)
        if len(a) < 60:
            continue
        for b, old in unique.items():
            if a == b:
                exact.append(dict(chapter_paragraph=p, sources=old['sources']))
                continue
            if not .5 <= len(b) / len(a) <= 2:
                continue
            matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
            if matcher.quick_ratio() < .88:
                continue
            ratio = matcher.ratio()
            if ratio < .88:
                continue
            edits = [dict(operation=op, current=a[i:j], earlier=b[k:l], current_offset=i)
                     for op, i, j, k, l in matcher.get_opcodes() if op != 'equal']
            changes.append(dict(chapter_paragraph=p, ratio=ratio, edits=edits,
                                earlier_text_sha256=hashlib.sha256(old['text'].encode()).hexdigest(),
                                sources=old['sources']))
    output = dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  status='Source comparison only; not a recovered answer',
                  source_manifest_date=manifest['retrieved_utc'], source_files=sources,
                  chapter_sha256=hashlib.sha256((ROOT/'wattpad-paragraphs.json').read_bytes()).hexdigest(),
                  normalized_corpus_paragraphs=len(unique), exact_matches=len(exact),
                  changed_paragraphs=sorted({x['chapter_paragraph'] for x in changes}),
                  changes=sorted(changes, key=lambda x: (x['chapter_paragraph'], -x['ratio'])))
    (HERE / 'source-audit.json').write_text(json.dumps(output, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
    print(json.dumps({k:v for k,v in output.items() if k not in ('source_files','changes')}, indent=2))
    for item in output['changes']:
        print(json.dumps(dict(paragraph=item['chapter_paragraph'], edits=item['edits'],
                              sources=[(s['kind'],s['id'],s['paragraph']) for s in item['sources']]), ensure_ascii=False))


if __name__ == '__main__':
    main()
