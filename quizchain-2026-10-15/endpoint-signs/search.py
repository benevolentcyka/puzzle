"""Finite public Quizchain test: recognize F...s/F...t/W...n/W...m globally.

Offline only. No prefix filter, no network, no signing or transactions.
Any recovered exact answer is written only to local FOUND-* files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import importlib.util
import itertools
import json
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
PAIRS = ['FS', 'FT', 'WN', 'WM']
EXPECTED = {'FS': [4, 92, 99, 167, 230], 'FT': [5, 93, 168, 231],
            'WN': [6, 51, 94, 138, 151, 156, 169, 232, 264],
            'WM': [7, 29, 95, 170, 234]}
GROUPS = [[4, 5, 6, 7], [92, 93, 94, 95], [167, 168, 169, 170], [230, 231, 232, 234]]
TARGETS = ['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W', '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']
PARENT = "m/44'/0'/0'/0"
FORMS = [
    ('draft-lf2', '\n\n', '\n', ' ', False),
    ('rendered-lf2', '\n\n', '\n', ' ', True),
    ('promoted-lf2', '\n\n', '\n\n', ' ', False),
    ('app-lf2', '\n\n', '\n', '\u00a0', False),
    ('draft-lf1', '\n', '\n', ' ', False),
    ('app-lf1', '\n', '\n', '\u00a0', False),
    ('draft-crlf2', '\r\n\r\n', '\n', ' ', False),
    ('normalized-crlf2', '\r\n\r\n', '\r\n', ' ', False),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
    temporary.replace(path)


def cpu_address(data, index=0):
    from bip_utils import Bip32Secp256k1, Bip39MnemonicGenerator, P2PKHAddrEncoder
    entropy = hashlib.md5(data).digest()
    words = str(Bip39MnemonicGenerator().FromEntropy(entropy))
    seed = hashlib.pbkdf2_hmac('sha512', words.encode(), b'mnemonic', 2048, 64)
    node = Bip32Secp256k1.FromSeed(seed).DerivePath(f'{PARENT}/{index}')
    address = P2PKHAddrEncoder.EncodeKey(node.PublicKey().RawCompressed().ToBytes(), net_ver=b'\x00')
    return address, node, words


def controls(repo):
    source = (repo / 'hal-finney-page.html').read_bytes().decode('latin1')
    body = re.search(r'<div class="post">([\s\S]*?)</div>', source)[1]
    body = re.sub(r'<br\s*/?>\s*<br\s*/?>', '\n\n', body, flags=re.I)
    body = re.sub(r'<br\s*/?>', '\n', body, flags=re.I)
    ps = html.unescape(re.sub('<[^>]*>', '', body)).strip().split('\n\n')
    assert len(ps) == 16
    for p, value in enumerate(ps):
        if value[0] not in 'ITASM':
            positions = [i for i, c in enumerate(value) if c in LETTERS]
            chars = list(value)
            chars[positions[0]] = chars[positions[0]].lower()
            chars[positions[-1]] = chars[positions[-1]].upper()
            ps[p] = ''.join(chars)
    stage = '\n\n'.join(ps).encode()
    posts = json.loads((repo / 'aoi-posts-archive.json').read_bytes())
    post = next(p['selftext'] for p in posts if p['id'] == 'bc6rkn')
    draft = post.split('hashing:\n\n', 1)[1].split('\n\nUpdate: Block solved', 1)[0]
    assert len(draft.split()) == 235
    block29 = (draft.replace('A pleasant female voice.', 'A pleasant female vOIce.', 1) + ' zff').encode()
    rows = []
    for label, data, expected_md5, expected_address in [
        ('Stage One reconstructed text', stage, '9dd2efb9bc976c2095bd534d7b8d431c', '19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN'),
        ('Grycoin Block 1', b'Still 21st Century', None, '18EpYz5qB3XoxZWouJF3KdEp3E2nfv9FgP'),
        ('Block 29 reconstructed draft', block29, '982301b80b30af3a0abe110269b0dd43', '1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P'),
    ]:
        digest = hashlib.md5(data).hexdigest()
        address, node, words = cpu_address(data)
        assert (expected_md5 is None or digest == expected_md5) and address == expected_address
        row = dict(control=label, md5=digest, address=address, bytes=len(data), passed=True)
        if label.startswith('Block 29'):
            from bip_utils import WifEncoder
            suffix = WifEncoder.Encode(node.PrivateKey().Raw().ToBytes())[-3:]
            assert suffix == 'JRu'
            row['wif_suffix'] = suffix
        rows.append(row)
    return rows


def select(ps, mask, include_headings, include_quote, recognition):
    chosen = []
    for p, text in enumerate(ps):
        positions = [i for i, c in enumerate(text) if c in LETTERS]
        if not positions:
            continue
        pair = text[positions[0]].upper() + text[positions[-1]].upper()
        if pair not in PAIRS or not (mask >> PAIRS.index(pair)) & 1:
            continue
        if not include_headings and p in [151, 156, 264]:
            continue
        if not include_quote and 230 <= p <= 234:
            continue
        if recognition == 'literal' and positions[0] != 0:
            continue
        chosen.append(p)
    return chosen


def materialize(ps, selected, style, form, start, tail):
    _, sep, internal, nbsp, trim = FORMS[form]
    out = []
    for p in range(start, len(ps)):
        text = ps[p]
        if p in selected:
            positions = [i for i, c in enumerate(text) if c in LETTERS]
            chars = list(text)
            if style in ['both', 'first']:
                chars[positions[0]] = chars[positions[0]].lower()
            if style in ['both', 'last']:
                chars[positions[-1]] = chars[positions[-1]].upper()
            text = ''.join(chars)
        text = text.replace('\u00a0', nbsp)
        if trim:
            text = '\n'.join(line.rstrip(' ') for line in text.split('\n'))
        out.append(text.replace('\n', internal))
    return (sep.join(out) + tail).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--platform', type=int, default=1)
    parser.add_argument('--batch', type=int, default=4096)
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error('Verification assertions must be enabled')
    if not 1 <= args.batch <= 32768:
        parser.error('batch must be 1..32768')
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    repo = args.repo.resolve()
    ps = json.loads((repo / 'wattpad-paragraphs.json').read_bytes())
    assert len(ps) == 273 and len('\n\n'.join(ps).encode()) == 45456
    found_pairs = {pair: [] for pair in PAIRS}
    for p, text in enumerate(ps):
        letters = ''.join(c for c in text if c in LETTERS)
        if letters and (pair := letters[0].upper() + letters[-1].upper()) in PAIRS:
            found_pairs[pair].append(p)
    assert found_pairs == EXPECTED
    baseline = materialize(ps, [p for g in GROUPS for p in g], 'both', 0, 0, '')
    assert sha(baseline) == '0648ab3455b4e2812e46ff80d527266bfb5bc8dfbf3850cf66f22115869c4732'
    control_results = controls(repo)
    print('PASS: source counts, exact pair indices, byte baseline and three reconstructed controls', flush=True)
    variants = []
    for mask, headings, quote, recognition, style in itertools.product(range(16), [True, False], [True, False], ['ascii', 'literal'], ['both', 'first', 'last']):
        variants.append(dict(pair_mask=mask, include_headings=headings, include_quote=quote,
                             recognition=recognition, style=style,
                             selected=select(ps, mask, headings, quote, recognition)))
    labels, entropies, seen = [], [], set()
    stream = hashlib.sha256()
    enumerated = 0
    for variant, form, start, tail in itertools.product(range(len(variants)), range(len(FORMS)), [0, 1, 3], ['', '\n']):
        v = variants[variant]
        data = materialize(ps, v['selected'], v['style'], form, start, tail)
        digest, fingerprint = hashlib.md5(data).digest(), hashlib.sha256(data).digest()
        enumerated += 1
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        stream.update(len(data).to_bytes(8, 'big') + data)
        labels.append(dict(variant=variant, form=form, start=start, tail=tail))
        entropies.append(digest)
    assert enumerated == 18432  # 128 selections x 3 case styles x 48 serializers
    indices = list(range(7))
    files = ['wattpad-paragraphs.json', 'hal-finney-page.html', 'aoi-posts-archive.json',
             'verifier.cjs', 'joint-format-2026-09-28/search.py',
             'expanded-2026-09-26/wallet_paths_gpu.py', 'assumptions-2026-09-27/search-assumptions.py']
    config = dict(family='global-endpoint-sign-pairs-v1', pairs=found_pairs, variants=variants,
                  forms=FORMS, starts=[0, 1, 3], tails=['', '\n'], indices=indices,
                  targets=TARGETS, parent=PARENT, entropy='raw-md5', language='english',
                  passphrase='', prefix_filter=None, candidate_stream_sha256=stream.hexdigest(),
                  files_sha256={p: sha((repo / p).read_bytes()) for p in files}, script_sha256=sha(Path(__file__).read_bytes()))
    # A full finite plan; no prior checkpoint is read or reused.
    write_json(args.output / 'plan.json', config)
    spec = importlib.util.spec_from_file_location('endpoint_wallet', repo / 'joint-format-2026-09-28/search.py')
    joint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(joint)
    wallet = joint.Wallet(args.platform, indices)
    config['gpu_kernel_sha256'] = wallet.A.CERT.gpu_kernel_fingerprint()
    config['wallet_kernel_sha256'] = wallet.gpu.kernel_sha256
    write_json(args.output / 'plan.json', config)
    result = dict(complete=False, enumeration_operations=enumerated, unique_buffers_sha256=len(labels),
                  unique_md5=len(set(entropies)), checked=0, addresses=0, matches=[], controls=control_results,
                  plan_sha256=sha((args.output / 'plan.json').read_bytes()), sampled_cpu_address_comparisons=0)
    write_json(args.output / 'results.json', result)
    print(f'{enumerated:,} operations; {len(labels):,} distinct buffers; seven indices; no prefix filter', flush=True)
    for offset in range(0, len(labels), args.batch):
        chunk = entropies[offset:offset + args.batch]
        words, seeds, output = wallet.derive(chunk, indices)
        samples = sorted({0, len(chunk) // 2, len(chunk) - 1})
        wallet.compare(words, seeds, output, [(k, chunk[k]) for k in samples], indices)
        for wanted, address in wallet.targets.items():
            for row in wallet.np.flatnonzero(wallet.np.all(output[0] == wallet.np.frombuffer(wanted, dtype=wallet.np.uint8), axis=1)):
                k, j = divmod(int(row), len(indices))
                label = labels[offset + k]
                v = variants[label['variant']]
                data = materialize(ps, v['selected'], v['style'], label['form'], label['start'], label['tail'])
                assert hashlib.md5(data).digest() == chunk[k]
                cpu, _, _ = cpu_address(data, indices[j])
                assert cpu == address
                dest = args.output / f'FOUND-endpoint-{offset+k}-i{indices[j]}.txt'
                dest.write_bytes(data)
                result['matches'].append(dict(address=address, index=indices[j], file=dest.name))
        result.update(checked=offset + len(chunk), addresses=(offset + len(chunk)) * len(indices),
                      complete=offset + len(chunk) == len(labels), sampled_cpu_address_comparisons=wallet.comparisons,
                      elapsed_seconds=time.monotonic() - started,
                      updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        write_json(args.output / 'results.json', result)
        print(f'{result["checked"]:,}/{len(labels):,}; matches={len(result["matches"])}', flush=True)
        if result['matches']:
            break
    print(json.dumps({k: v for k, v in result.items() if k != 'controls'}), flush=True)


if __name__ == '__main__':
    main()
