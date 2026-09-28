"""Structured-twist search on draft-calibrated chapter serializations.

Calibration (see README): the reproduced block 29 control shows the author's
draft -> hash path is raw UTF-8, LF, MD5, no trailing newline. The chapter's six
NBSPs are all NBSP+space and every trailing run is one space, the signature of
typed double spaces converted to HTML; the author's own Reddit copies of the
Abstract carry two ASCII spaces. The broad radius/pair sweeps did not combine
that base with paragraph-level or motif case twists, although the author said
the revised answer removed only "one of the twists I had".

Per base: FFWW group masks, flip styles, subsets of eight nearby non-FFWW
paragraphs (the "I" of "I STNM", the example's "I" hypothetical, "Next"),
motifs from the author's own long-text answers (block 29 "vOIce", title
"SECOND"), and any one or two further paragraph flips. No MD5-prefix filter.
English BIP39 from raw MD5, empty passphrase, m/44'/0'/0'/0/0, both targets.
Read-only: no network access, no transactions. Matches are saved only in
git-ignored FOUND-* files after independent CPU confirmation.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import itertools
import json
import multiprocessing
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARAS = json.loads((ROOT / 'wattpad-paragraphs.json').read_bytes())
GROUPS = [[4, 5, 6, 7], [92, 93, 94, 95], [167, 168, 169, 170], [230, 231, 232, 234]]
IN_GROUPS = {p for g in GROUPS for p in g}
MASKS = [15, 7, 0] + [m for m in range(16) if m not in (15, 7, 0)]
NEAR = [3, 8, 9, 91, 164, 165, 166, 233]  # I/N paragraphs adjacent to the four groups
MOTIFS = ['vOIce11', 'vOIce23', 'SECOND0']
TARGETS = ['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W', '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']
PARENT = "m/44'/0'/0'/0"
# (name, join, nbsp, tails, internal) -- tails 'trim' also drops spaces before an internal break
SERIALIZATIONS = [
    ('draft', '\n\n', ' ', 'keep', '\n'),
    ('rendered', '\n\n', ' ', 'trim', '\n'),
    ('draft-promoted', '\n\n', ' ', 'keep', '\n\n'),
    ('app', '\n\n', ' ', 'keep', '\n'),
    ('draft-single', '\n', ' ', 'keep', '\n'),
    ('rendered-single', '\n', ' ', 'trim', '\n'),
    ('app-single', '\n', ' ', 'keep', '\n'),
]
BASES = [dict(name=n, join=j, nbsp=s, tails=t, internal=b, start=start)
         for n, j, s, t, b in SERIALIZATIONS for start in (0, 1, 3)]
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def letters(text):
    return [i for i, c in enumerate(text) if c in LETTERS]


ENDS = {p: (ls[0], ls[-1]) for p, ls in ((p, letters(t)) for p, t in enumerate(PARAS)) if ls}


def motif_ops(name):
    """Character-level (paragraph, char index, case) operations."""
    if name == 'SECOND0':
        assert PARAS[0] == 'Second'
        return [(0, i, 'upper') for i in range(6)]
    p = {'vOIce11': 11, 'vOIce23': 23}[name]
    k = PARAS[p].index('voice')
    assert PARAS[p].count('voice') == 1
    return [(p, k + 1, 'upper'), (p, k + 2, 'upper')]


def pattern_ops(pattern):
    mask, style, extra, motifs = pattern
    ops = []
    for bit, group in enumerate(GROUPS):
        if mask >> bit & 1:
            for p in group:
                first, last = ENDS[p]
                if style in ('both', 'first'):
                    ops.append((p, first, 'lower'))
                if style in ('both', 'last'):
                    ops.append((p, last, 'upper'))
    for p in extra:
        first, last = ENDS[p]
        ops += [(p, first, 'lower'), (p, last, 'upper')]
    for m in motifs:
        ops += motif_ops(m)
    seen = {}
    for p, i, case in ops:
        if seen.get((p, i), case) != case:
            return None  # contradictory request (e.g. SECOND with a flipped title)
        seen[(p, i)] = case
    return sorted((p, i, c) for (p, i), c in seen.items())


def patterns(start):
    """Deterministic enumeration; duplicates are removed later by digest."""
    others = [p for p in range(start, len(PARAS)) if p not in IN_GROUPS and p in ENDS]
    near = [p for p in NEAR if p >= start]
    motifs = [m for m in MOTIFS if not (m == 'SECOND0' and start > 0)]
    subsets = lambda xs, k: itertools.chain.from_iterable(itertools.combinations(xs, r) for r in range(k + 1))
    for mask in MASKS:  # phase A: flip styles x nearby paragraphs x motifs
        for style in ('both', 'first', 'last'):
            for extra in subsets(near, len(near)):
                for mot in subsets(motifs, len(motifs)):
                    yield (mask, style, extra, mot)
    for mask in MASKS:  # phase B: any one or two further paragraphs
        for extra in subsets(others, 2):
            yield (mask, 'both', extra, ())
    for mask in (15, 7):  # phase C: motifs with any one further paragraph
        for mot in subsets(motifs, len(motifs)):
            if mot:
                for extra in subsets(others, 1):
                    yield (mask, 'both', extra, mot)


def serialize(base, cased):
    """Independent character-level serializer from (possibly re-cased) paragraphs."""
    out = []
    for p in range(base['start'], len(PARAS)):
        t = cased[p].replace(' ', base['nbsp'])
        if base['tails'] == 'trim':
            t = '\n'.join(line.rstrip(' ') for line in t.split('\n'))
        out.append(t.replace('\n', base['internal']))
    return base['join'].join(out).encode('utf8')


def reference(base, pattern):
    ops = pattern_ops(pattern)
    cased = [list(p) for p in PARAS]
    for p, i, case in ops:
        cased[p][i] = cased[p][i].upper() if case == 'upper' else cased[p][i].lower()
    return serialize(base, [''.join(c) for c in cased])


class Fast:
    """Base bytes plus byte offsets of every character; ASCII case edits keep lengths."""

    def __init__(self, base):
        self.base = base
        self.source = serialize(base, PARAS)
        self.offset = {}
        position, sep = 0, base['join'].encode()
        for p in range(base['start'], len(PARAS)):
            text = PARAS[p].replace(' ', base['nbsp'])
            if base['tails'] == 'trim':
                text = '\n'.join(line.rstrip(' ') for line in text.split('\n'))
            text = text.replace('\n', base['internal'])
            # map original letter indices to serialized byte offsets (letters are never removed)
            orig = [i for i in letters(PARAS[p])]
            ser = [i for i, c in enumerate(text) if c in LETTERS]
            assert len(orig) == len(ser)
            prefix = [len(text[:i].encode('utf8')) for i in ser]
            for o, b in zip(orig, prefix):
                self.offset[(p, o)] = position + b
            position += len(text.encode('utf8')) + (len(sep) if p < len(PARAS) - 1 else 0)
        assert position == len(self.source)

    def digest(self, pattern, buffer):
        ops = pattern_ops(pattern)
        if ops is None:
            return None
        saved = []
        for p, i, case in ops:
            o = self.offset[(p, i)]
            saved.append((o, buffer[o]))
            c = buffer[o]
            buffer[o] = (c & ~32) if case == 'upper' else (c | 32)
        d = hashlib.md5(buffer).digest()
        for o, c in saved:
            buffer[o] = c
        return d


_worker = {}


def _init(base_index):
    fast = Fast(BASES[base_index])
    _worker['fast'], _worker['buffer'] = fast, bytearray(fast.source)


def _digests(chunk):
    return [_worker['fast'].digest(p, _worker['buffer']) for p in chunk]


def build_base(index, pool_size):
    pats = list(patterns(BASES[index]['start']))
    with multiprocessing.Pool(pool_size, initializer=_init, initargs=(index,)) as pool:
        chunks = [pats[i:i + 4096] for i in range(0, len(pats), 4096)]
        digests = [d for part in pool.map(_digests, chunks) for d in part]
    unique, keep = {}, []
    for pat, d in zip(pats, digests):
        if d is not None and d not in unique:
            unique[d] = len(keep)
            keep.append((pat, d))
    return keep, len(pats)


def load_joint():
    spec = importlib.util.spec_from_file_location('joint', ROOT / 'joint-format-2026-09-28/search.py')
    joint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(joint)
    return joint


def self_test():
    rng = random.Random(29)
    checks = 0
    # Independent anchors: the byte-audited canonical four-group LF base, and its NBSP->space form.
    canonical = (ROOT / 'bases/four-groups-lflf.txt').read_bytes()
    app0 = next(i for i, b in enumerate(BASES) if b['name'] == 'app' and b['start'] == 0)
    draft0 = next(i for i, b in enumerate(BASES) if b['name'] == 'draft' and b['start'] == 0)
    assert reference(BASES[app0], (15, 'both', (), ())) == canonical
    assert reference(BASES[draft0], (15, 'both', (), ())) == canonical.decode('utf8').replace(' ', ' ').encode()
    checks += 2
    for index, base in enumerate(BASES):
        fast = Fast(base)
        buf = bytearray(fast.source)
        pats = list(patterns(base['start']))
        for pat in [pats[0], pats[-1]] + rng.sample(pats, 60):
            d = fast.digest(pat, buf)
            if d is not None:
                assert d == hashlib.md5(reference(base, pat)).digest(), (base, pat)
                checks += 1
        assert bytes(buf) == fast.source
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', type=int, default=1)
    parser.add_argument('--batch', type=int, default=16384)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error('Do not use python -O: verification assertions must remain enabled')
    checks = self_test()
    print(f'PASS: {checks} independent serializer/MD5 comparisons across {len(BASES)} bases', flush=True)
    if args.verify_only:
        return
    joint = load_joint()
    wallet = joint.Wallet(args.platform, [0])  # Stage One + Grycoin Block 1 positive controls
    from bip_utils import Base58Decoder, Bip32Secp256k1
    from bip39_gpu.gpu.bip32_gpu import base58check_encode, hash160_to_p2pkh
    np = wallet.np
    # Block 29 long-text control through this exact matching path.
    words, seeds, out = wallet.derive([bytes.fromhex('982301b80b30af3a0abe110269b0dd43')], [0])
    assert out[0][0].tobytes() == Base58Decoder.CheckDecode('1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P')[1:], 'Block 29 control failed'
    wanted = {Base58Decoder.CheckDecode(a)[1:]: a for a in TARGETS}
    code = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), ROOT / 'joint-format-2026-09-28/search.py']}
    config = dict(family='calibrated-structured-twists-v1', bases=BASES, groups=GROUPS, near=NEAR, motifs=MOTIFS,
                  targets=TARGETS, path=f'{PARENT}/0', entropy='raw MD5 UTF-8', language='english', passphrase='',
                  prefix_filter=None, source_sha256=hashlib.sha256((ROOT / 'wattpad-paragraphs.json').read_bytes()).hexdigest(),
                  code_sha256=code, gpu_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(), wallet_kernel_sha256=wallet.gpu.kernel_sha256)
    tag = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
    dest = HERE / f'twist-search-{tag}.json'
    state = json.loads(dest.read_bytes()) if dest.exists() else dict(configuration=config, next_base=0, bases=[], matches=[], complete=False)
    if state['configuration'] != config:
        raise RuntimeError('Checkpoint identity mismatch; refusing to resume')
    print(f'Checkpoint {dest.name}: resume at base {state["next_base"]}/{len(BASES)}', flush=True)
    begun = time.monotonic()
    while state['next_base'] < len(BASES) and not state['matches']:
        index = state['next_base']
        base = BASES[index]
        t0 = time.monotonic()
        keep, enumerated = build_base(index, args.workers)
        for start in range(0, len(keep), args.batch):
            chunk = keep[start:start + args.batch]
            entropies = [d for _, d in chunk]
            words, seeds, out = wallet.derive(entropies, [0])
            sample = sorted({0, len(chunk) // 2, len(chunk) - 1})
            wallet.compare(words, seeds, out, [(k, entropies[k]) for k in sample], [0])
            for k in sample:
                assert hashlib.md5(reference(base, chunk[k][0])).digest() == entropies[k]
            for raw, address in wanted.items():
                for r in np.flatnonzero(np.all(out[0] == np.frombuffer(raw, dtype=np.uint8), axis=1)):
                    pat, entropy = chunk[int(r)]
                    text = reference(base, pat)
                    assert hashlib.md5(text).digest() == entropy
                    seed = hashlib.pbkdf2_hmac('sha512', words[int(r)].encode(), b'mnemonic', 2048, 64)
                    node = Bip32Secp256k1.FromSeed(seed).DerivePath(f'{PARENT}/0')
                    pub = node.PublicKey().RawCompressed().ToBytes()
                    assert hash160_to_p2pkh(hashlib.new('ripemd160', hashlib.sha256(pub).digest()).digest()) == address
                    found = HERE / f'FOUND-twist-{tag}-{base["name"]}-p{base["start"]}.txt'
                    found.write_bytes(text)
                    found.with_suffix('.json').write_text(json.dumps(dict(address=address, base=base, pattern=pat,
                        md5=entropy.hex(), mnemonic=words[int(r)],
                        wif=base58check_encode(b'\x80' + node.PrivateKey().Raw().ToBytes() + b'\x01')), indent=2))
                    state['matches'].append(dict(address=address, base=base, file=found.name))
                    print(f'VERIFIED MATCH saved privately in {found}', flush=True)
        state['bases'].append(dict(base=base, enumerated=enumerated, distinct_entropies=len(keep),
                                   seconds=round(time.monotonic() - t0, 1)))
        state['next_base'] += 1
        state['complete'] = state['next_base'] == len(BASES)
        state['derived_addresses'] = sum(b['distinct_entropies'] for b in state['bases'])
        state['sampled_cpu_comparisons'] = state.get('sampled_cpu_comparisons', 0) + wallet.comparisons
        wallet.comparisons = 0
        state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        wallet.A.CERT.atomic_json(dest, state)
        print(f'base {index + 1}/{len(BASES)} {base["name"]} p{base["start"]}: {len(keep):,} distinct of {enumerated:,} '
              f'in {time.monotonic() - t0:.0f}s; total {state["derived_addresses"]:,}; elapsed {time.monotonic() - begun:.0f}s', flush=True)
    print('VERIFIED MATCH' if state['matches'] else 'COMPLETE, no match in this bounded family' if state['complete'] else 'STOPPED', flush=True)


if __name__ == '__main__':
    main()
