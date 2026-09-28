"""Grycoin Block 2 answer windows that extend into the surrounding post text.

Precedent: the verified Stage One buffer includes the post's trailing line
"[edited slightly]", which the author did not describe and later said she did
not know. For the example she likewise said she did not know how the winner
went from the capitalization to the prize. Earlier example searches deleted or
duplicated spans inside the question, but never extended it into adjacent
post paragraphs ("Question:", "Format: [solution]", and so on).

Every contiguous window of the archived post's paragraphs that contains the
whole question × the six prior case rules applied to question paragraphs only
or to every window paragraph × LF/CRLF paragraph joins × optional final
newline. BIP44 indices 0-6, English raw MD5, no hint filter; 3c6-prefix
survivors are listed for information only. Read-only.
"""
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TARGET = '1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def recase(p, rule):
    chars = list(p)
    pos = [j for j, c in enumerate(chars) if c.isascii() and c.isalpha()]
    if not pos:
        return p
    if (rule.startswith('ffww') and p[0] in 'FW') or (rule == 'non-itasm' and p[0] not in 'ITASM'):
        chars[pos[0]] = chars[pos[0]].lower()
        chars[pos[-1]] = chars[pos[-1]].swapcase() if rule == 'ffww-toggle' else chars[pos[-1]].upper()
    if rule in ('named', 'ffww-and-named') and 'post outing himself.' in p:
        chars[0] = chars[0].lower()
        chars[p.index('post outing himself.') + len('post outing himself') - 1] = 'F'
    return ''.join(chars)


def candidates():
    posts = json.loads((ROOT / 'aoi-posts-archive.json').read_bytes())
    post = next(x for x in posts if x['id'] == 'cleczc')['selftext']
    paras = post.split('\n\n')
    question = post.split('Question:\n\n', 1)[1].split('\n\nFormat:', 1)[0].split('\n\n')
    qa = next(i for i in range(len(paras)) if paras[i:i + len(question)] == question)
    qb = qa + len(question) - 1
    assert hashlib.md5('\n\n'.join(paras[qa:qb + 1]).encode()).hexdigest() == '7759227d7406d8230d7e3a8f7b9846d7'
    for a, b in itertools.product(range(qa + 1), range(qb, len(paras))):
        for rule in ['none', 'ffww', 'ffww-toggle', 'non-itasm', 'named', 'ffww-and-named']:
            for scope in ['question', 'window']:
                if scope == 'window' and rule == 'none':
                    continue
                window = [recase(p, rule) if (scope == 'window' or qa <= i <= qb) else p
                          for i, p in enumerate(paras[a:b + 1], a)]
                for join in ['\n\n', '\r\n\r\n']:
                    body = join.join(p.replace('\n', join[:len(join) // 2]) for p in window)
                    for tail in ['', join[:len(join) // 2]]:
                        yield (body + tail).encode(), dict(window=[a, b], question=[qa, qb], rule=rule, scope=scope,
                                                          join='lf' if join == '\n\n' else 'crlf', tail=bool(tail))


def main():
    if sys.flags.optimize:
        raise SystemExit('Do not use python -O')
    joint = module('joint', ROOT / 'joint-format-2026-09-28/search.py')
    wallet = joint.Wallet(1, [0])
    from bip_utils import Base58Decoder
    seen, items = set(), []
    for data, label in candidates():
        d = hashlib.md5(data).digest()
        if d not in seen:
            seen.add(d)
            items.append((label, d, data))
    indices = list(range(7))
    entropies = [d for _, d, _ in items]
    words, seeds, out = wallet.derive(entropies, indices)
    wallet.compare(words, seeds, out, [(k, entropies[k]) for k in (0, len(items) // 2, len(items) - 1)], indices)
    wanted = wallet.np.frombuffer(Base58Decoder.CheckDecode(TARGET)[1:], dtype=wallet.np.uint8)
    hits = [dict(items[int(r) // 7][0], index=int(r) % 7)
            for r in wallet.np.flatnonzero(wallet.np.all(out[0] == wanted, axis=1))]
    prefix = [dict(label, md5=d.hex()) for label, d, _ in items if d.hex().startswith('3c6')]
    if hits:
        found = HERE / 'FOUND-example-context.json'
        found.write_text(json.dumps(dict(hits=hits, texts=[items[int(r) // 7][2].decode() for r in
            wallet.np.flatnonzero(wallet.np.all(out[0] == wanted, axis=1))]), indent=2))
        print('MATCH saved to', found)
    result = dict(family='example-context-windows-v1', target=TARGET, distinct_entropies=len(items),
                  indices='0-6', addresses=len(items) * 7, matches=hits, prefix_3c6_survivors=prefix)
    (HERE / 'example-context-result.json').write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps(dict(distinct=len(items), matches=hits, prefix_3c6=len(prefix))))


if __name__ == '__main__':
    main()
