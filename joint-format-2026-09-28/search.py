"""Bounded, resumable mixed-format search of the public Quizchain chapter.

Combine two or three local deviations from coherent serialization baselines,
requiring at least two artifact classes: trailing spaces, NBSPs, internal breaks.
No MD5-prefix filter; no network requests or transactions. All targets are the
two public puzzle addresses. A match is verified independently and saved locally.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import functools
import hashlib
import importlib.util
import itertools
import json
import math
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GROUPS = [[4, 5, 6, 7], [92, 93, 94, 95], [167, 168, 169, 170], [230, 231, 232, 234]]
TARGETS = ['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W', '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']
PARENT = "m/44'/0'/0'/0"
TOKEN = re.compile(r'\u00a0|\n| +$')
SOURCES = json.loads((ROOT / 'wattpad-paragraphs.json').read_bytes())
MASKS = [15, 7, 0] + [i for i in range(16) if i not in [15, 7, 0]]
# CRLF joins are first because of the author's explicit 13,10,13,10 clarification.
FORMS = [('crlf', 'crlf'), ('lf', 'lf'), ('crlf', 'lf')]
BASES = [dict(group_mask=g, start=s, join=j, internal=b, tails=t, nbsp=n)
         for g in MASKS for s in [0, 1, 3] for j, b in FORMS
         for t in ['keep', 'trim'] for n in ['keep', 'space', 'delete']]


def flip(paragraph):
    letters = [i for i, c in enumerate(paragraph) if c.isascii() and c.isalpha()]
    result = list(paragraph)
    result[letters[0]] = result[letters[0]].lower()
    result[letters[-1]] = result[letters[-1]].upper()
    return ''.join(result)


def kind(value):
    return 'nbsp' if value == '\u00a0' else 'break' if value == '\n' else 'tail'


def options(value, label):
    """Return the baseline first, then every other distinct representation."""
    k = kind(value)
    sep = '\n\n' if label['join'] == 'lf' else '\r\n\r\n'
    if k == 'tail':
        choices = [value, '']
        default = value if label['tails'] == 'keep' else ''
    elif k == 'nbsp':
        choices = ['\u00a0', ' ', '']
        default = {'keep': '\u00a0', 'space': ' ', 'delete': ''}[label['nbsp']]
    else:
        choices = ['\n', '\r\n', '', ' ', sep]
        default = '\n' if label['internal'] == 'lf' else '\r\n'
    assert len(choices) == len(set(choices))
    return [default] + [x for x in choices if x != default]


class Base:
    def __init__(self, label):
        self.label = label
        sep = b'\n\n' if label['join'] == 'lf' else b'\r\n\r\n'
        selected = {p for bit, group in enumerate(GROUPS) if label['group_mask'] & (1 << bit) for p in group}
        parts, length, state = [], 0, hashlib.md5()
        self.sites, self.prefixes = [], []

        def append(value):
            nonlocal length
            parts.append(value)
            state.update(value)
            length += len(value)

        for p in range(label['start'], len(SOURCES)):
            if p > label['start']:
                append(sep)
            paragraph = flip(SOURCES[p]) if p in selected else SOURCES[p]
            cursor = 0
            for match in TOKEN.finditer(paragraph):
                append(paragraph[cursor:match.start()].encode('utf8'))
                choices = [x.encode('utf8') for x in options(match.group(), label)]
                self.prefixes.append(state.copy())
                self.sites.append(dict(paragraph=p, char_offset=match.start(), kind=kind(match.group()),
                                       start=length, end=length + len(choices[0]), choices=choices))
                append(choices[0])
                cursor = match.end()
            append(paragraph[cursor:].encode('utf8'))
        self.source = b''.join(parts)
        self.view = memoryview(self.source)
        assert len(self.sites) == 29

    def digest(self, edits):
        # Fixed prefixes are copied, then only the suffix containing changes is hashed.
        md = self.prefixes[edits[0][0]].copy()
        cursor = self.sites[edits[0][0]]['start']
        for index, option in edits:
            site = self.sites[index]
            md.update(self.view[cursor:site['start']])
            md.update(site['choices'][option])
            cursor = site['end']
        md.update(self.view[cursor:])
        return md.digest()

    def witness(self, edits):
        parts, cursor = [], 0
        for index, option in edits:
            site = self.sites[index]
            parts.extend([self.source[cursor:site['start']], site['choices'][option]])
            cursor = site['end']
        return b''.join(parts + [self.source[cursor:]])

    def metadata(self, edits):
        return dict(self.label, edits=[dict(site=i, paragraph=self.sites[i]['paragraph'],
            char_offset=self.sites[i]['char_offset'], kind=self.sites[i]['kind'],
            original_hex=self.sites[i]['choices'][0].hex(), replacement_hex=self.sites[i]['choices'][c].hex())
            for i, c in edits])


@functools.lru_cache(maxsize=4)
def base(index):
    return Base(BASES[index])


@functools.lru_cache(maxsize=2)
def patterns(degree):
    sites = base(0).sites
    result = []
    for indices in itertools.combinations(range(len(sites)), degree):
        if len({sites[i]['kind'] for i in indices}) < 2:
            continue
        for choices in itertools.product(*(range(1, len(sites[i]['choices'])) for i in indices)):
            result.append(tuple(zip(indices, choices)))
    return result


def independent_count(degree):
    # Select counts from each of the three categories, independent of the enumerator.
    total = 0
    for t in range(degree + 1):
        for n in range(degree + 1 - t):
            b = degree - t - n
            if sum(x > 0 for x in [t, n, b]) < 2:
                continue
            total += math.comb(13, t) * math.comb(6, n) * 2**n * math.comb(10, b) * 4**b
    return total


def locate(rank, maximum=3):
    for degree in range(2, maximum + 1):
        per_base = len(patterns(degree))
        if rank < len(BASES) * per_base:
            b, p = divmod(rank, per_base)
            return base(b), patterns(degree)[p]
        rank -= len(BASES) * per_base
    raise IndexError('Candidate rank outside this search')


def reference(label, edits):
    """Separate, character-based serializer: no byte offsets or cached prefixes."""
    selected = {p for bit, group in enumerate(GROUPS) if label['group_mask'] & (1 << bit) for p in group}
    override, site, paragraphs = dict(edits), 0, []
    for p in range(label['start'], len(SOURCES)):
        text = SOURCES[p]
        if p in selected:
            first = next(i for i, c in enumerate(text) if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
            last = max(i for i, c in enumerate(text) if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
            text = text[:first] + text[first].lower() + text[first + 1:last] + text[last].upper() + text[last + 1:]
        output, offset = [], 0
        for match in TOKEN.finditer(text):
            output.append(text[offset:match.start()])
            output.append(options(match.group(), label)[override.get(site, 0)])
            site += 1
            offset = match.end()
        paragraphs.append(''.join(output) + text[offset:])
    sep = '\n\n' if label['join'] == 'lf' else '\r\n\r\n'
    return sep.join(paragraphs).encode('utf8')


def verify_serialization():
    assert len(SOURCES) == 273 and len(BASES) == 864
    assert Counter(s['kind'] for s in base(0).sites) == dict(tail=13, nbsp=6, **{'break': 10})
    for degree, expected in [(2, 1156), (3, 31476)]:
        pats = patterns(degree)
        assert len(pats) == len(set(pats)) == independent_count(degree) == expected
        assert all(len(p) == degree and len({base(0).sites[i]['kind'] for i, _ in p}) >= 2 for p in pats)
    rng = random.Random(777)
    comparisons = 0
    for index, label in enumerate(BASES):
        b = base(index)
        assert b.source == reference(label, ())
        assert [s['kind'] for s in b.sites] == [s['kind'] for s in base(0).sites]
        for degree in [2, 3]:
            edits = patterns(degree)[rng.randrange(len(patterns(degree)))]
            expected = reference(label, edits)
            assert b.witness(edits) == expected and b.digest(edits) == hashlib.md5(expected).digest()
            comparisons += 1
    # Explicit boundaries, including the transition between degrees and bases.
    boundaries = {0, 1155, 1156, 864 * 1156 - 1, 864 * 1156, 864 * (1156 + 31476) - 1}
    for rank in sorted(boundaries):
        b, p = locate(rank)
        assert b.digest(p) == hashlib.md5(reference(b.label, p)).digest()
        comparisons += 1
    return comparisons


def load_wallet_support():
    sys.path.insert(0, str(ROOT / 'expanded-2026-09-26'))
    spec = importlib.util.spec_from_file_location('joint_assumptions', ROOT / 'assumptions-2026-09-27/search-assumptions.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Wallet:
    def __init__(self, platform, indices):
        self.A = load_wallet_support()
        import numpy as np
        from bip39_gpu.gpu import context, pbkdf2_gpu
        from bip_utils import Base58Decoder
        from wallet_paths_gpu import WalletPathsGPU
        context._global_context = context.GPUContext(platform_id=platform)
        pbkdf2_gpu._pbkdf2_cpu_fallback = self.A.CERT.die_fallback
        self.pbkdf2, self.indices, self.np = pbkdf2_gpu, indices, np
        self.gpu = WalletPathsGPU(context._global_context)
        self.certified = self.gpu.certify([dict(name='bip44', parent=PARENT, hardened=False, direct=False)])
        self.targets = {Base58Decoder.CheckDecode(a)[1:]: a for a in TARGETS}
        self.comparisons = 0
        self.controls()

    def derive(self, entropies, indices):
        words = [self.A.mnemonic(e) for e in entropies]
        seeds = self.pbkdf2.pbkdf2_hmac_sha512_gpu(
            [self.A.HELPER.normalized_password(w) for w in words], [b'mnemonic'] * len(words))
        output = self.gpu.batch(seeds, PARENT, indices)
        assert output[0].shape == (len(entropies) * len(indices), 20)
        return words, seeds, output

    def compare(self, words, seeds, output, sample, indices):
        from bip_utils import Bip32Secp256k1, Bip39MnemonicGenerator
        hashes, keys, pubs = output
        for k, entropy in sample:
            assert str(Bip39MnemonicGenerator().FromEntropy(entropy)) == words[k]
            seed = hashlib.pbkdf2_hmac('sha512', words[k].encode(), b'mnemonic', 2048, 64)
            assert seed == seeds[k], 'Independent PBKDF2 mismatch'
            for j, index in enumerate(indices):
                node = Bip32Secp256k1.FromSeed(seed).DerivePath(f'{PARENT}/{index}')
                pub = node.PublicKey().RawCompressed().ToBytes()
                h = hashlib.new('ripemd160', hashlib.sha256(pub).digest()).digest()
                r = k * len(indices) + j
                assert hashes[r].tobytes() == h and keys[r].tobytes() == node.PrivateKey().Raw().ToBytes() and pubs[r].tobytes() == pub, 'Independent BIP32 mismatch'
                self.comparisons += 1

    def controls(self):
        from bip_utils import Base58Decoder
        entropies = [bytes.fromhex('9dd2efb9bc976c2095bd534d7b8d431c'), hashlib.md5(b'Still 21st Century').digest()]
        words, seeds, out = self.derive(entropies, [0])
        self.compare(words, seeds, out, list(enumerate(entropies)), [0])
        for k, expected in enumerate(['19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN', '18EpYz5qB3XoxZWouJF3KdEp3E2nfv9FgP']):
            wanted = Base58Decoder.CheckDecode(expected)[1:]
            assert out[0][k].tobytes() == wanted, 'Solved positive control failed'
            assert k in self.np.flatnonzero(self.np.all(out[0] == self.np.frombuffer(wanted, dtype=self.np.uint8), axis=1)), 'Positive matching control failed'

    def check(self, start, entropies, config, maximum, tag):
        from bip_utils import Bip32Secp256k1
        from bip39_gpu.gpu.bip32_gpu import base58check_encode, hash160_to_p2pkh
        words, seeds, out = self.derive(entropies, self.indices)
        sample = sorted({0, len(entropies) // 2, len(entropies) - 1})
        for k in sample:
            b, p = locate(start + k, maximum)
            assert hashlib.md5(reference(b.label, p)).digest() == entropies[k]
        self.compare(words, seeds, out, [(k, entropies[k]) for k in sample], self.indices)
        matches = []
        for wanted, address in self.targets.items():
            for r in self.np.flatnonzero(self.np.all(out[0] == self.np.frombuffer(wanted, dtype=self.np.uint8), axis=1)):
                k, j = divmod(int(r), len(self.indices))
                b, p = locate(start + k, maximum)
                witness = reference(b.label, p)
                assert witness == b.witness(p) and hashlib.md5(witness).digest() == entropies[k]
                seed = hashlib.pbkdf2_hmac('sha512', words[k].encode(), b'mnemonic', 2048, 64)
                path = f'{PARENT}/{self.indices[j]}'
                node = Bip32Secp256k1.FromSeed(seed).DerivePath(path)
                pub = node.PublicKey().RawCompressed().ToBytes()
                assert hash160_to_p2pkh(hashlib.new('ripemd160', hashlib.sha256(pub).digest()).digest()) == address
                dest = HERE / f'FOUND-joint-{tag}-rank{start + k}-index{self.indices[j]}.txt'
                dest.write_bytes(witness)
                self.A.CERT.atomic_json(dest.with_suffix('.json'), dict(address=address, path=path,
                    md5=entropies[k].hex(), mnemonic=words[k], private_wif=base58check_encode(b'\x80' + node.PrivateKey().Raw().ToBytes() + b'\x01'),
                    rank=start + k, metadata=b.metadata(p), configuration=config))
                matches.append(dict(address=address, rank=start + k, file=dest.name))
                print(f'VERIFIED MATCH: saved privately in {dest}', flush=True)
        return matches


@contextlib.contextmanager
def exclusive(path):
    """OS lock is released on exit/crash; an old lock file is harmless."""
    with path.open('a+b') as handle:
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if sys.platform == 'win32':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-edits', type=int, choices=[2, 3], default=3)
    parser.add_argument('--indices', default='0', help='Comma-separated BIP44 address indices; default 0')
    parser.add_argument('--platform', type=int, default=1)
    parser.add_argument('--batch', type=int, default=16384)
    parser.add_argument('--limit', type=int, help='Additional candidates this invocation, then checkpoint and stop')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error('Do not use python -O: verification assertions must remain enabled')
    try:
        indices = [int(i) for i in args.indices.split(',')]
    except ValueError:
        parser.error('Indices must be comma-separated integers')
    if not indices or len(set(indices)) != len(indices) or any(i < 0 or i >= 2**31 for i in indices):
        parser.error('Use distinct nonhardened indices')
    if args.batch < 1 or args.batch > 65536 or (args.limit is not None and args.limit < 1):
        parser.error('Batch must be 1..65536; limit must be positive')
    checks = verify_serialization()
    total = len(BASES) * sum(independent_count(d) for d in range(2, args.max_edits + 1))
    print(f'PASS: {checks:,} full-text serialization/MD5 comparisons, 864 baselines, independent combinatorial counts', flush=True)
    print(f'Total: {total:,} candidate instances; {total * len(indices):,} address operations; indices={indices}; no prefix filter', flush=True)
    if args.verify_only:
        return
    wallet = Wallet(args.platform, indices)
    code_files = [Path(__file__), ROOT / 'gpu-case-pairs.py', ROOT / 'expanded-2026-09-26/wallet_paths_gpu.py',
                  ROOT / 'assumptions-2026-09-27/search-assumptions.py', ROOT / 'followup-2026-09-26/language-settings-gpu.py',
                  ROOT / 'followup-2026-09-26/verification/languages/english.json']
    config = dict(family='joint-observed-formatting-v1', max_edits=args.max_edits, min_artifact_classes=2,
        indices=indices, targets=TARGETS, parent=PARENT, language='english', passphrase='', entropy='raw MD5 UTF-8',
        final_newline=False, prefix_filter=None, baselines=BASES,
        source_sha256=hashlib.sha256((ROOT / 'wattpad-paragraphs.json').read_bytes()).hexdigest(),
        code_sha256={str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files},
        gpu_kernel_sha256=wallet.A.CERT.gpu_kernel_fingerprint(), wallet_kernel_sha256=wallet.gpu.kernel_sha256)
    tag = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
    dest = HERE / f'joint-format-{tag}.json'
    with exclusive(dest.with_suffix('.lock')):
        state = json.loads(dest.read_bytes()) if dest.exists() else dict(configuration=config, candidates_total=total,
            next_rank=0, derived_addresses=0, matches=[], complete=False, elapsed_search_seconds=0.0, sampled_cpu_comparisons=0)
        if state['configuration'] != config or state['candidates_total'] != total or not 0 <= state['next_rank'] <= total:
            raise RuntimeError('Checkpoint identity/count mismatch')
        if state['derived_addresses'] != state['next_rank'] * len(indices) or state['complete'] != (state['next_rank'] == total):
            raise RuntimeError('Inconsistent checkpoint progress')
        print(f'Checkpoint: {dest.name}; resume at {state["next_rank"]:,}/{total:,}; startup BIP32 checks={wallet.certified}', flush=True)
        if state['complete'] or state['matches']:
            print('Already complete, no match.' if state['complete'] and not state['matches'] else 'A verified match was already saved; inspect local FOUND files.', flush=True)
            return
        initial = state['next_rank']
        stop = min(total, initial + args.limit) if args.limit else total
        begun = last = time.monotonic()
        accumulated = state['elapsed_search_seconds']
        old_comparisons = state['sampled_cpu_comparisons']
        sample_start = wallet.comparisons
        try:
            while state['next_rank'] < stop:
                start = state['next_rank']
                size = min(args.batch, stop - start)
                entropies = []
                for rank in range(start, start + size):
                    b, p = locate(rank, args.max_edits)
                    entropies.append(b.digest(p))
                matches = wallet.check(start, entropies, config, args.max_edits, tag)
                state['next_rank'] += size
                state['derived_addresses'] += size * len(indices)
                state['matches'].extend(matches)
                state['complete'] = state['next_rank'] == total
                state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                state['elapsed_search_seconds'] = accumulated + time.monotonic() - begun
                state['sampled_cpu_comparisons'] = old_comparisons + wallet.comparisons - sample_start
                state['serialization_comparisons_per_startup'] = checks
                state['positive_controls_passed'] = ['stage-one', 'grycoin-one']
                wallet.A.CERT.atomic_json(dest, state)
                now = time.monotonic()
                if now - last >= 20 or state['next_rank'] == stop or matches:
                    speed = (state['next_rank'] - initial) / (now - begun)
                    remaining = (total - state['next_rank']) / speed
                    print(f'candidates={state["next_rank"]:,}/{total:,} addresses={state["derived_addresses"]:,} rate={speed:,.0f}/s elapsed={now - begun:.1f}s remaining~{remaining / 60:.1f}min matches={len(state["matches"])}', flush=True)
                    last = now
                if matches:
                    break
        except KeyboardInterrupt:
            print(f'Interrupted; last committed rank {state["next_rank"]:,}. Run the same command to resume; at most one batch repeats.', flush=True)
            return
        print('VERIFIED MATCH saved locally' if state['matches'] else 'COMPLETE, no match in this bounded family' if state['complete'] else 'LIMIT reached; run without --limit to resume', flush=True)


if __name__ == '__main__':
    main()
