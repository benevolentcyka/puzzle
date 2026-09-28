"""Per-boundary line-break slips in the format example and the final chapter.

Evidence: the author doubles paragraph breaks by hand ("Hit enter twice"; for
the example "I added the extra line breaks between paragraphs ... before
hashing") and demonstrably misses some. The published chapter keeps ten single
breaks as <br>, and paragraph 183 is two paragraphs of the 2019-07-17 part
"THOMAS and SATOSHI" merged by one. Earlier example searches used one global
join; earlier chapter searches changed only the ten known <br> sites.

Example (target 1tzie...): each of its nine paragraph boundaries independently
"\n", "\n\n" or "\n\n\n" (3**9) under the six case rules of
assumptions-2026-09-27/search-assumptions.py; BIP44 indices 0-6; no hint filter.
Chapter (both final targets): calibrated twist-search.py bases draft/rendered/app,
starts 0/1/3, all-four and first-three FFWW; one or two slipped sites, where a
paragraph boundary becomes "\n" or "\n\n\n" and an internal <br> becomes "\n\n".
Index 0. Read-only; matches only in git-ignored FOUND-* files.
"""
import hashlib
import importlib.util
import itertools
import json
import multiprocessing
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXAMPLE_TARGET = '1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


twist = module('twist', HERE / 'twist-search.py')


def example_rules():
    posts = json.loads((ROOT / 'aoi-posts-archive.json').read_bytes())
    q = next(x for x in posts if x['id'] == 'cleczc')['selftext'].split('Question:\n\n', 1)[1].split('\n\nFormat:', 1)[0]
    assert hashlib.md5(q.encode()).hexdigest() == '7759227d7406d8230d7e3a8f7b9846d7'
    out = {}
    for rule in ['none', 'ffww', 'ffww-toggle', 'non-itasm', 'named', 'ffww-and-named']:
        paras = q.split('\n\n')
        for i, p in enumerate(paras):
            chars = list(p)
            pos = [j for j, c in enumerate(chars) if c.isascii() and c.isalpha()]
            if (rule.startswith('ffww') and p[0] in 'FW') or (rule == 'non-itasm' and p[0] not in 'ITASM'):
                chars[pos[0]] = chars[pos[0]].lower()
                chars[pos[-1]] = chars[pos[-1]].swapcase() if rule == 'ffww-toggle' else chars[pos[-1]].upper()
            if rule in ('named', 'ffww-and-named') and 'post outing himself.' in p:
                chars[0] = chars[0].lower()
                chars[p.index('post outing himself.') + len('post outing himself') - 1] = 'F'
            paras[i] = ''.join(chars)
        assert len(paras) == 10
        out[rule] = paras
    return out


def example_candidates():
    for rule, paras in example_rules().items():
        for seps in itertools.product(['\n\n', '\n', '\n\n\n'], repeat=9):
            text = paras[0] + ''.join(s + p for s, p in zip(seps, paras[1:]))
            yield text.encode(), dict(rule=rule, seps=[len(s) for s in seps])


def chapter_label(base_index, mask, slips):
    return dict(base=base_index, mask=mask, slips=slips)


def chapter_text(base_index, mask, slips):
    """Independent rebuild: explicit per-boundary separators, then the base rules."""
    base = twist.BASES[base_index]
    ops = twist.pattern_ops((mask, 'both', (), ()))
    cased = [list(p) for p in twist.PARAS]
    for p, i, case in ops:
        cased[p][i] = cased[p][i].upper() if case == 'upper' else cased[p][i].lower()
    paras = []
    for p in range(base['start'], len(twist.PARAS)):
        t = ''.join(cased[p]).replace(' ', base['nbsp'])
        if base['tails'] == 'trim':
            t = '\n'.join(line.rstrip(' ') for line in t.split('\n'))
        pieces = t.split('\n')
        out = pieces[0]
        for k, piece in enumerate(pieces[1:]):
            out += slips.get(('br', p, k), base['internal']) + piece
        paras.append(out)
    text = paras[0]
    for k, p in enumerate(paras[1:]):
        text += slips.get(('join', base['start'] + k + 1), base['join']) + p
    return text.encode('utf8')


def chapter_sites(base_index):
    base = twist.BASES[base_index]
    sites = [(('join', p), alt) for p in range(base['start'] + 1, len(twist.PARAS)) for alt in ['\n', '\n\n\n']]
    for p in range(base['start'], len(twist.PARAS)):
        for k in range(twist.PARAS[p].count('\n')):
            sites.append((('br', p, k), '\n\n'))
    return sites


def chapter_patterns(base_index):
    sites = chapter_sites(base_index)
    for mask in (15, 7):
        yield mask, ()
        for a in range(len(sites)):
            yield mask, (a,)
        for a, b in itertools.combinations(range(len(sites)), 2):
            if sites[a][0] != sites[b][0]:
                yield mask, (a, b)


_w = {}


def _init(base_index):
    _w['base'], _w['sites'] = base_index, chapter_sites(base_index)


def _digest(chunk):
    out = []
    for mask, picks in chunk:
        slips = {_w['sites'][i][0]: _w['sites'][i][1] for i in picks}
        out.append(hashlib.md5(chapter_text(_w['base'], mask, slips)).digest())
    return out


def run(wallet, items, indices, targets, tag, rebuild):
    np = wallet.np
    from bip_utils import Base58Decoder, Bip32Secp256k1
    wanted = {Base58Decoder.CheckDecode(a)[1:]: a for a in targets}
    hits = []
    for start in range(0, len(items), 16384):
        chunk = items[start:start + 16384]
        entropies = [d for _, d in chunk]
        words, seeds, out = wallet.derive(entropies, indices)
        sample = sorted({0, len(chunk) // 2, len(chunk) - 1})
        wallet.compare(words, seeds, out, [(k, entropies[k]) for k in sample], indices)
        for k in sample:
            assert hashlib.md5(rebuild(chunk[k][0])).digest() == entropies[k]
        for raw, address in wanted.items():
            for r in np.flatnonzero(np.all(out[0] == np.frombuffer(raw, dtype=np.uint8), axis=1)):
                k, j = divmod(int(r), len(indices))
                label, entropy = chunk[k]
                text = rebuild(label)
                assert hashlib.md5(text).digest() == entropy
                seed = hashlib.pbkdf2_hmac('sha512', words[k].encode(), b'mnemonic', 2048, 64)
                node = Bip32Secp256k1.FromSeed(seed).DerivePath(f"m/44'/0'/0'/0/{indices[j]}")
                found = HERE / f'FOUND-slips-{tag}-{start + k}.txt'
                found.write_bytes(text)
                found.with_suffix('.json').write_text(json.dumps(dict(address=address, index=indices[j], label=str(label),
                    md5=entropy.hex(), mnemonic=words[k], private_hex=node.PrivateKey().Raw().ToHex()), indent=2))
                hits.append(dict(address=address, index=indices[j], file=found.name))
                print('VERIFIED MATCH', found, flush=True)
    return hits


def main():
    if sys.flags.optimize:
        raise SystemExit('Do not use python -O')
    joint = module('joint', ROOT / 'joint-format-2026-09-28/search.py')
    wallet = joint.Wallet(1, [0])
    # The six example rules must reproduce the prior search's all-double-LF bases exactly.
    prior = {m['rule']: m['source'] for _, m in wallet.A.span_bases() if m['join'] == 'lf'}
    mine = {r: '\n\n'.join(p).encode() for r, p in example_rules().items()}
    assert prior == mine
    for bi, base in enumerate(twist.BASES):
        for mask in (15, 7):
            assert chapter_text(bi, mask, {}) == twist.reference(base, (mask, 'both', (), ()))
    b0 = next(i for i, b in enumerate(twist.BASES) if b['name'] == 'draft' and b['start'] == 0)
    plain = twist.reference(twist.BASES[b0], (15, 'both', (), ()))
    assert chapter_text(b0, 15, {('join', 1): '\n'}) == plain.replace(b'Second\n\nI. Second', b'Second\nI. Second', 1)
    result = dict(family='linebreak-slips-v1', example={}, chapter={})
    t0 = time.monotonic()
    seen, items = set(), []
    for text, label in example_candidates():
        d = hashlib.md5(text).digest()
        if d not in seen:
            seen.add(d)
            items.append(((label, text), d))
    hits = run(wallet, items, list(range(7)), [EXAMPLE_TARGET], 'example', lambda lt: lt[1])
    result['example'] = dict(distinct_entropies=len(items), indices='0-6', addresses=len(items) * 7, matches=hits,
                             seconds=round(time.monotonic() - t0, 1))
    print('example', json.dumps({k: v for k, v in result['example'].items()}), flush=True)
    bases = [i for i, b in enumerate(twist.BASES) if b['name'] in ('draft', 'rendered', 'app')]
    total = 0
    for bi in bases:
        t1 = time.monotonic()
        pats = list(chapter_patterns(bi))
        with multiprocessing.Pool(8, initializer=_init, initargs=(bi,)) as pool:
            digests = [d for part in pool.map(_digest, [pats[i:i + 2048] for i in range(0, len(pats), 2048)]) for d in part]
        sites = chapter_sites(bi)
        seen, items = set(), []
        for (mask, picks), d in zip(pats, digests):
            if d not in seen:
                seen.add(d)
                items.append(((mask, picks), d))
        rebuild = lambda lab, bi=bi, sites=sites: chapter_text(bi, lab[0], {sites[i][0]: sites[i][1] for i in lab[1]})
        hits = run(wallet, items, [0], twist.TARGETS, f'chapter-b{bi}', rebuild)
        total += len(items)
        result['chapter'][str(bi)] = dict(base=twist.BASES[bi], distinct_entropies=len(items), matches=hits,
                                          seconds=round(time.monotonic() - t1, 1))
        print('chapter base', bi, twist.BASES[bi]['name'], twist.BASES[bi]['start'], len(items), 'matches', len(hits), flush=True)
        if hits:
            break
    result['chapter_total_addresses'] = total
    result['sampled_cpu_comparisons'] = wallet.comparisons
    (HERE / 'linebreak-slips-result.json').write_text(json.dumps(result, indent=1) + '\n')
    print('DONE', json.dumps(dict(example=result['example']['matches'], chapter_total=total)), flush=True)


if __name__ == '__main__':
    main()
