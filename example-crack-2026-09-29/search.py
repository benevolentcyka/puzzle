"""Unfiltered bounded case-toggle search for the SOLVED example (Grycoin Block 2).

The example prize (1tzie…, 700k sats) was claimed in 2019, so an exact answer
buffer exists. The author said knowing it helps the final block but that she
does not know how the solver claimed it. Earlier large case-mask sweeps on the
example derived only `3c6`-prefix survivors into wallets; this derives EVERY
candidate (no prefix filter) and targets the real address.

Family: from each plausible baseline serialization, apply every combination of
up to `--max-toggles` ASCII-letter case flips over all 1,197 letters. Baselines
differ only in which sign paragraphs get first-lower/last-upper. LF LF joins
(the form that reproduced the author's published 7759227 prefix). Compares the
example address and, for free, both final prize addresses. Index 0 by default
(the example is a bare "[solution]", first key). Read-only; any hit is
CPU-reconfirmed and written only to a git-ignored FOUND-* file.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXAMPLE = '1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'
PRIZES = ['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W', '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def example_paragraphs():
    posts = json.loads((ROOT / 'aoi-posts-archive.json').read_bytes())
    q = next(x for x in posts if x['id'] == 'cleczc')['selftext'].split('Question:\n\n', 1)[1].split('\n\nFormat:', 1)[0]
    paras = q.split('\n\n')
    assert len(paras) == 10 and hashlib.md5(q.encode()).hexdigest() == '7759227d7406d8230d7e3a8f7b9846d7'
    return paras


def first_last(p):
    idx = [j for j, c in enumerate(p) if c in LETTERS]
    return idx[0], idx[-1]


def baseline_text(paras, name):
    """Return the LF LF-joined baseline bytes for a named sign-selection."""
    sign = {
        'raw': set(),
        'ffww-quad': {2, 3, 6, 7},          # the four F,F,W,W paragraphs
        'non-itasm': {2, 3, 5, 6, 7},        # every paragraph not starting I/T/A/S/M
        'author': {2, 3, 6, 7},              # ffww-quad plus the described himself/I edits below
    }[name]
    out = [list(p) for p in paras]
    for i in sign:
        a, b = first_last(paras[i])
        out[i][a] = out[i][a].lower()
        out[i][b] = out[i][b].upper()
    if name == 'author':
        # "changing 'I' to 'i' and 'himself' to 'himselF'": para 4 'I' start and the f of 'himself'
        out[4][0] = 'i'
        k = paras[4].index('himself')
        out[4][k + 6] = 'F'
    return '\n\n'.join(''.join(c) for c in out).encode('utf8')


def letter_offsets(text):
    return [i for i, b in enumerate(text) if 65 <= b <= 90 or 97 <= b <= 122]


def candidates(base_bytes, offsets, max_toggles):
    """Yield (combo, md5digest); combo is a tuple of toggled byte offsets."""
    buf = bytearray(base_bytes)
    for k in range(0, max_toggles + 1):
        for combo in itertools.combinations(offsets, k):
            for o in combo:
                buf[o] ^= 32
            yield combo, hashlib.md5(buf).digest()
            for o in combo:
                buf[o] ^= 32


def rebuild(base_bytes, combo):
    buf = bytearray(base_bytes)
    for o in combo:
        buf[o] ^= 32
    return bytes(buf)


def load_wallet(indices, platform):
    spec = importlib.util.spec_from_file_location('joint', ROOT / 'joint-format-2026-09-28/search.py')
    joint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(joint)
    return joint.Wallet(platform, indices)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', choices=['raw', 'ffww-quad', 'non-itasm', 'author'], default='ffww-quad')
    ap.add_argument('--max-toggles', type=int, default=3)
    ap.add_argument('--indices', default='0')
    ap.add_argument('--platform', type=int, default=1)
    ap.add_argument('--batch', type=int, default=32768)
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    if sys.flags.optimize:
        ap.error('Do not use python -O')
    indices = [int(i) for i in args.indices.split(',')]
    paras = example_paragraphs()
    base = baseline_text(paras, args.baseline)
    offsets = letter_offsets(base)
    n = len(offsets)
    total = sum(_comb(n, k) for k in range(args.max_toggles + 1))
    # Independent enumeration/serialization checks on bounded, directly-drawn combos.
    import random
    rng = random.Random(2019)
    checks = 0
    probe = [()] + [(o,) for o in offsets[:20]]
    probe += [tuple(sorted(rng.sample(offsets, 2))) for _ in range(60)]
    probe += [tuple(sorted(rng.sample(offsets, min(3, args.max_toggles)))) for _ in range(60)]
    for combo in probe:
        assert hashlib.md5(rebuild(base, combo)).digest() == hashlib.md5(bytes(_toggled(base, combo))).digest()
        assert all(base[o] ^ 32 == rebuild(base, combo)[o] for o in combo)
        checks += 1
    # The first batch of the generator must agree with rebuild().
    for i, (combo, digest) in enumerate(candidates(base, offsets, args.max_toggles)):
        assert digest == hashlib.md5(rebuild(base, combo)).digest()
        checks += 1
        if i >= 500:
            break
    print(f'baseline={args.baseline} md5={hashlib.md5(base).hexdigest()} letters={n} '
          f'candidates={total:,} (<= {args.max_toggles} toggles) indices={indices}', flush=True)
    print(f'PASS: {checks} independent serialization checks', flush=True)
    if args.verify_only:
        return
    wallet = load_wallet(indices, args.platform)
    from bip_utils import Base58Decoder, Bip32Secp256k1
    from bip39_gpu.gpu.bip32_gpu import base58check_encode, hash160_to_p2pkh
    np = wallet.np
    targets = {Base58Decoder.CheckDecode(a)[1:]: a for a in [EXAMPLE] + PRIZES}
    state_path = HERE / f'example-{args.baseline}-t{args.max_toggles}-i{"-".join(map(str, indices))}.json'
    done = json.loads(state_path.read_bytes()) if state_path.exists() else dict(
        baseline=args.baseline, baseline_md5=hashlib.md5(base).hexdigest(), max_toggles=args.max_toggles,
        indices=indices, candidates_total=total, next_rank=0, derived=0, matches=[], complete=False)
    if done['baseline_md5'] != hashlib.md5(base).hexdigest() or done['candidates_total'] != total:
        raise RuntimeError('Checkpoint mismatch')
    begin = time.monotonic()
    gen = candidates(base, offsets, args.max_toggles)
    # Skip already-checked candidates on resume.
    for _ in range(done['next_rank']):
        next(gen)
    seen_batch = []
    rank = done['next_rank']
    combo_buf, ent_buf = [], []

    def flush():
        nonlocal rank
        if not ent_buf:
            return
        words, seeds, out = wallet.derive(ent_buf, indices)
        s = sorted({0, len(ent_buf) // 2, len(ent_buf) - 1})
        wallet.compare(words, seeds, out, [(k, ent_buf[k]) for k in s], indices)
        for k in s:
            assert hashlib.md5(rebuild(base, combo_buf[k])).digest() == ent_buf[k]
        for raw, address in targets.items():
            for r in np.flatnonzero(np.all(out[0] == np.frombuffer(raw, dtype=np.uint8), axis=1)):
                ki, j = divmod(int(r), len(indices))
                combo = combo_buf[ki]
                text = rebuild(base, combo)
                assert hashlib.md5(text).digest() == ent_buf[ki]
                seed = hashlib.pbkdf2_hmac('sha512', words[ki].encode(), b'mnemonic', 2048, 64)
                node = Bip32Secp256k1.FromSeed(seed).DerivePath(f"m/44'/0'/0'/0/{indices[j]}")
                assert hash160_to_p2pkh(hashlib.new('ripemd160', hashlib.sha256(node.PublicKey().RawCompressed().ToBytes()).digest()).digest()) == address
                fp = HERE / f'FOUND-example-{args.baseline}-{address[:8]}.txt'
                fp.write_bytes(text)
                fp.with_suffix('.json').write_text(json.dumps(dict(address=address, baseline=args.baseline,
                    toggled_offsets=list(combo), index=indices[j], md5=ent_buf[ki].hex(), mnemonic=words[ki],
                    wif=base58check_encode(b'\x80' + node.PrivateKey().Raw().ToBytes() + b'\x01')), indent=2))
                done['matches'].append(dict(address=address, baseline=args.baseline, index=indices[j], file=fp.name))
                print(f'VERIFIED MATCH: {fp}', flush=True)
        rank += len(ent_buf)
        combo_buf.clear()
        ent_buf.clear()

    for combo, digest in gen:
        combo_buf.append(combo)
        ent_buf.append(digest)
        if len(ent_buf) >= args.batch:
            flush()
            done['next_rank'] = rank
            done['derived'] = rank * len(indices)
            done['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            wallet.A.CERT.atomic_json(state_path, done)
            if done['matches']:
                break
            if rank % (args.batch * 40) < args.batch:
                sp = (rank - done.get('_start', 0) or rank) / max(time.monotonic() - begin, 1e-9)
                print(f'{rank:,}/{total:,} ({100 * rank / total:.1f}%) ~{sp:,.0f}/s eta~{(total - rank) / sp / 60:.0f}min', flush=True)
    flush()
    done['next_rank'] = rank
    done['complete'] = rank >= total
    wallet.A.CERT.atomic_json(state_path, done)
    print('VERIFIED MATCH' if done['matches'] else 'COMPLETE, no match' if done['complete'] else 'STOPPED', flush=True)


def _comb(n, k):
    from math import comb
    return comb(n, k)


def _toggled(base, combo):
    buf = bytearray(base)
    for o in combo:
        buf[o] ^= 32
    return buf


if __name__ == '__main__':
    main()
