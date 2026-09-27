"""Finite tests of copied text, hash algorithms and the historical entropy field.

This does not expand a case radius. Source-span searches optionally rely on the
example's published MD5 prefix; digest and algorithm searches never do. Winning
witnesses are independently verified and written only under ignored FOUND names.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import importlib.util
import itertools
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'bip39-gpu-review/src'))
TARGETS = {'example': ['1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'],
           'chapter': ['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W', '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


HELPER = module('historical_candidates', ROOT / 'followup-2026-09-26/language-settings-gpu.py')
CERT = module('arithmetic_certifier', ROOT / 'gpu-case-pairs.py')
WORDS = json.loads((ROOT / 'followup-2026-09-26/verification/languages/english.json').read_bytes())['words']


def mnemonic(entropy):
    if not entropy or len(entropy) % 4:
        raise ValueError('Historical entropy must contain whole 32-bit units')
    bits = ''.join(f'{b:08b}' for b in entropy)
    checksum = ''.join(f'{b:08b}' for b in hashlib.sha256(entropy).digest())[:len(entropy) // 4]
    bits += checksum
    return ' '.join(WORDS[int(bits[i:i+11], 2)] for i in range(0, len(bits), 11))


def historical_raw(text):
    """2019 auto-detection followed by its keep-the-last-whole-32-bits rule."""
    digits = ''.join(re.findall('[0-9a-f]', text.lower()))
    if not digits:
        return b''
    if set(digits) <= set('01'):
        base, clean = 2, digits
    elif len(re.findall('[a2-9tjqk][cdhs]', text.lower())) >= len(digits) / 2:
        # Never silently claim this branch was covered by the hexadecimal model.
        raise ValueError('Historical converter detects playing cards; add an exact card adapter')
    elif set(digits) <= set('123456'):
        base, clean = 6, digits.replace('6', '0')
    elif set(digits) <= set('012345'):
        base, clean = 6, digits
    elif set(digits) <= set('0123456789'):
        base, clean = 10, digits
    else:
        base, clean = 16, digits
    value = int(clean, base)
    width = max(value.bit_length(), math.floor(len(clean) * math.log2(base)))
    width = width // 32 * 32
    return (value & ((1 << width) - 1)).to_bytes(width // 8, 'big') if width else b''


def entry_variants(md):
    h = md.hex()
    yield h, {'edit': 'unchanged'}
    for i, old in enumerate(h):
        for c in '0123456789abcdef':
            if c != old:
                yield h[:i] + c + h[i+1:], {'edit': 'replace-hex', 'offset': i, 'new': c}
        yield h[:i] + h[i+1:], {'edit': 'delete-hex', 'offset': i}
    for i in range(len(h) + 1):
        for c in '0123456789abcdef':
            yield h[:i] + c + h[i:], {'edit': 'insert-hex', 'offset': i, 'new': c}
    for i in range(len(h) - 1):
        if h[i] != h[i+1]:
            yield h[:i] + h[i+1] + h[i] + h[i+2:], {'edit': 'transpose-hex', 'offset': i}
    for n in [8, 16, 24]:
        yield h[:n], {'edit': 'prefix', 'hex_length': n}
        yield h[-n:], {'edit': 'suffix', 'hex_length': n}
    yield h * 2, {'edit': 'double-paste'}
    yield h[::-1], {'edit': 'reverse-hex'}
    yield md[::-1].hex(), {'edit': 'reverse-bytes'}


def algorithm_variants(source):
    for algorithm in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'ripemd160']:
        raw = hashlib.new(algorithm, source).digest()
        yield raw, {'algorithm': algorithm, 'mode': 'full'}
        if len(raw) > 32:
            for n in [16, 20, 24, 28, 32]:
                yield raw[:n], {'algorithm': algorithm, 'mode': 'prefix', 'bytes': n}
                yield raw[-n:], {'algorithm': algorithm, 'mode': 'suffix', 'bytes': n}
    md = hashlib.md5(source).digest()
    for name, data in [('digest', md), ('hex-lower', md.hex().encode()), ('hex-upper', md.hex().upper().encode())]:
        for algorithm in ['md5', 'sha1', 'sha256']:
            yield hashlib.new(algorithm, data).digest(), {'algorithm': algorithm, 'input': 'md5-' + name}


def span_bases():
    posts = json.loads((ROOT / 'aoi-posts-archive.json').read_bytes())
    q = next(x for x in posts if x['id'] == 'cleczc')['selftext'].split('Question:\n\n', 1)[1].split('\n\nFormat:', 1)[0]
    assert hashlib.md5(q.encode()).hexdigest() == '7759227d7406d8230d7e3a8f7b9846d7'
    for rule in ['none', 'ffww', 'ffww-toggle', 'non-itasm', 'named', 'ffww-and-named']:
        paras = q.split('\n\n')
        for i, p in enumerate(paras):
            chars = list(p)
            positions = [j for j, c in enumerate(chars) if c.isascii() and c.isalpha()]
            selected = (rule.startswith('ffww') and p[0] in 'FW') or (rule == 'non-itasm' and p[0] not in 'ITASM')
            if selected:
                chars[positions[0]] = chars[positions[0]].lower()
                chars[positions[-1]] = chars[positions[-1]].swapcase() if rule == 'ffww-toggle' else chars[positions[-1]].upper()
            if rule in ['named', 'ffww-and-named'] and 'post outing himself.' in p:
                chars[0] = chars[0].lower()
                chars[p.index('post outing himself.') + len('post outing himself') - 1] = 'F'
            paras[i] = ''.join(chars)
        for join, sep in [('lf', '\n\n'), ('crlf', '\r\n\r\n')]:
            source = sep.join(paras).encode()
            yield hashlib.md5(source).digest(), {'rule': rule, 'join': join, 'source': source}


def source_variants(source, scope):
    # Boundaries before and after words/whitespace/punctuation preserve exact bytes.
    boundaries = sorted({0, len(source)} | {v for m in re.finditer(rb'\s+|\w+|[^\w\s]+', source) for v in m.span()})
    if scope == 'bytes':
        boundaries = range(len(source) + 1)
    for start, end in itertools.combinations(boundaries, 2):
        yield source[:start] + source[end:], {'edit': 'delete-span', 'start': start, 'end': end}
        yield source[:end] + source[start:end] + source[end:], {'edit': 'duplicate-span', 'start': start, 'end': end}
    # Treat the quoted examples as linked edits, including more than three letters.
    quoted = [i for m in re.finditer(rb'"[^"\r\n]*"', source) for i in range(m.start()+1, m.end()-1)
              if 65 <= source[i] <= 90 or 97 <= source[i] <= 122]
    groups = [quoted, [i for i in quoted if source[i] in b'Ii'], [i for i in quoted if source[i] in b'Nn'],
              [i for i, c in enumerate(source) if c in b'Ii'], [i for i, c in enumerate(source) if c in b'FfWw']]
    for group, offsets in enumerate(groups):
        for mode in ['lower', 'upper', 'toggle']:
            work = bytearray(source)
            for i in offsets:
                work[i] = source[i] | 32 if mode == 'lower' else source[i] & ~32 if mode == 'upper' else source[i] ^ 32
            yield bytes(work), {'edit': 'linked-case', 'group': group, 'mode': mode}


def certify_historical():
    inputs = ['ab' * n for n in [4, 8, 12, 16, 20, 24, 28, 32, 48, 64]]
    inputs += ['0123456789' * 4, '012345' * 8, '123456' * 8, '01' * 64]
    for h in ['2941774a2abec9f30c7d6777d1d53d91', '9dd2efb9bc976c2095bd534d7b8d431c']:
        variants = list(entry_variants(bytes.fromhex(h)))
        inputs += [h] + [variants[i][0] for i in range(0, len(variants), 13)]
    cp = subprocess.run(['node', str(HERE / 'historical-input.cjs')], input=json.dumps(inputs),
                        text=True, capture_output=True, check=True, cwd=ROOT)
    expected = json.loads(cp.stdout)
    for item in expected:
        raw = historical_raw(item['input'])
        if raw.hex() != item['entropy'] or (mnemonic(raw) if raw else '') != item['words']:
            raise RuntimeError('Historical 2019 input/mnemonic mismatch')
    return len(expected)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--family', choices=['hash-entry', 'hash-algorithm', 'source-spans'], required=True)
    ap.add_argument('--target', choices=['example', 'chapter', 'both'], default='both')
    ap.add_argument('--indices', default='0,1,2,3,4,5,6')
    ap.add_argument('--scope', choices=['tokens', 'bytes'], default='tokens')
    ap.add_argument('--unfiltered', action='store_true', help='Source spans only: do not require the 3c6 MD5 hint')
    ap.add_argument('--platform', type=int, default=1)
    ap.add_argument('--batch', type=int, default=4096)
    ap.add_argument('--limit-bases', type=int, help='Process at most this many previously unfinished source bases')
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    indices = [int(x) for x in args.indices.split(',')]
    if not indices or len(set(indices)) != len(indices) or any(i < 0 or i >= 2**31 for i in indices):
        ap.error('Use distinct valid nonhardened indices')
    if args.batch < 1 or (args.limit_bases is not None and args.limit_bases < 1):
        ap.error('Batch and limit must be positive')
    comparisons = certify_historical()
    print(f'PASS: {comparisons} input/mnemonic comparisons against preserved 2019 JavaScript', flush=True)
    if args.verify_only:
        return
    from bip39_gpu.gpu import context, pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs, hash160_to_p2pkh, base58check_encode
    from bip_utils import Bip32Secp256k1, Base58Decoder
    context._global_context = context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback = CERT.die_fallback
    for index in indices:
        CERT.certify_gpu(index)
    candidates = []
    families = ['example', 'chapter'] if args.target == 'both' else [args.target]
    if args.family == 'source-spans':
        if args.target == 'chapter':
            ap.error('Source-span mode is calibrated on the example only')
        candidates = [('example', md, label) for md, label in span_bases()]
    else:
        for family in families:
            data = HELPER.canonical_example_candidates() if family == 'example' else HELPER.chapter_candidates()
            candidates += [(family, md, label) for md, label in data]
    stream = hashlib.sha256()
    for family, md, label in candidates:
        stream.update(family.encode() + b'\0' + label['source'] + b'\0')
    config = {'family': args.family, 'target': args.target, 'indices': indices, 'scope': args.scope,
              'prefix_filter': '3c6' if args.family == 'source-spans' and not args.unfiltered else None,
              'candidate_stream_sha256': stream.hexdigest(), 'source_bases': len(candidates),
              'gpu_kernel_sha256': CERT.gpu_kernel_fingerprint(), 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'mnemonic_language': 'english', 'passphrase': '', 'path': "m/44'/0'/0'/0/INDEX",
              'historical_js_comparisons': comparisons}
    tag = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
    state_path = HERE / f'{args.family}-{args.target}-{tag}.json'
    state = json.loads(state_path.read_bytes()) if state_path.exists() else {
        'configuration': config, 'next_base': 0, 'attempted_variants': 0,
        'derived_entropies': 0, 'derived_addresses': 0, 'matches': 0, 'complete': False}
    if state['configuration'] != config:
        raise RuntimeError('Checkpoint configuration differs')
    target_map = {Base58Decoder.CheckDecode(a)[1:]: a for f in families for a in TARGETS[f]}
    begun = time.monotonic()
    last_log = begun

    def derive(batch, family, original, source_label):
        nonlocal last_log
        words = [mnemonic(e) for e, _, _ in batch]
        seeds = pbkdf2_gpu.pbkdf2_hmac_sha512_gpu([HELPER.normalized_password(w) for w in words], [b'mnemonic'] * len(words))
        sampled = sorted({0, len(batch)//2, len(batch)-1})
        for k in sampled:
            if hashlib.pbkdf2_hmac('sha512', words[k].encode(), b'mnemonic', 2048, 64) != seeds[k]:
                raise RuntimeError('Sampled seed mismatch')
        for index in indices:
            output = batch_seed_to_gpu_outputs(seeds, address_index=index)
            if output is None or len(output[0]) != len(batch):
                raise RuntimeError('GPU output unavailable or wrong size')
            hashes, _, _ = output
            for k in sampled:
                node = Bip32Secp256k1.FromSeed(seeds[k]).DerivePath(f"m/44'/0'/0'/0/{index}")
                public = node.PublicKey().RawCompressed().ToBytes()
                independent = hashlib.new('ripemd160', hashlib.sha256(public).digest()).digest()
                if bytes(hashes[k]) != independent:
                    raise RuntimeError('Sampled address mismatch')
            for k, value in enumerate(hashes):
                address = target_map.get(bytes(value))
                if address not in TARGETS[family]:
                    continue
                # Recompute the seed and private key on CPU before saving a witness.
                seed = hashlib.pbkdf2_hmac('sha512', words[k].encode(), b'mnemonic', 2048, 64)
                node = Bip32Secp256k1.FromSeed(seed).DerivePath(f"m/44'/0'/0'/0/{index}")
                public = node.PublicKey().RawCompressed().ToBytes()
                if hash160_to_p2pkh(hashlib.new('ripemd160', hashlib.sha256(public).digest()).digest()) != address:
                    raise RuntimeError('Hit failed independent validation')
                entropy, edit, witness = batch[k]
                dest = HERE / f'FOUND-{args.family}-{family}.txt'
                dest.write_bytes(witness)
                CERT.atomic_json(dest.with_suffix('.json'), {'address': address, 'index': index, 'entropy': entropy.hex(),
                    'mnemonic': words[k], 'private_wif': base58check_encode(b'\x80' + node.PrivateKey().Raw().ToBytes() + b'\x01'),
                    'source': {a:b for a,b in source_label.items() if a != 'source'}, 'edit': edit,
                    'source_md5': hashlib.md5(witness).hexdigest(), 'configuration': config})
                state['matches'] += 1
                CERT.atomic_json(state_path, state)
                print(f'VERIFIED MATCH saved privately at {dest}', flush=True)
                raise SystemExit(0)
        state['derived_entropies'] += len(batch)
        state['derived_addresses'] += len(batch) * len(indices)
        if time.monotonic() - last_log >= 20:
            print(f"bases={state['next_base']}/{len(candidates)} addresses={state['derived_addresses']:,} elapsed={time.monotonic()-begun:.1f}s", flush=True)
            last_log = time.monotonic()

    start = state['next_base']
    stop = min(len(candidates), start + args.limit_bases) if args.limit_bases else len(candidates)
    print(f"{state_path.name}; starting base {start}/{len(candidates)}; prefix filter={config['prefix_filter']}", flush=True)
    for rank in range(start, stop):
        family, md, label = candidates[rank]
        source = label['source']
        seen = set()
        batch = []
        if args.family == 'hash-entry':
            variants = ((historical_raw(text), edit, source) for text, edit in entry_variants(md))
        elif args.family == 'hash-algorithm':
            variants = ((entropy, edit, source) for entropy, edit in algorithm_variants(source))
        else:
            variants = ((hashlib.md5(text).digest(), edit, text) for text, edit in source_variants(source, args.scope))
        for entropy, edit, witness in variants:
            state['attempted_variants'] += 1
            if not entropy or entropy in seen:
                continue
            if config['prefix_filter'] and not entropy.hex().startswith(config['prefix_filter']):
                continue
            seen.add(entropy)
            batch.append((entropy, edit, witness))
            if len(batch) >= args.batch:
                derive(batch, family, source, label)
                batch = []
        if batch:
            derive(batch, family, source, label)
        state['next_base'] = rank + 1
        state['complete'] = rank + 1 == len(candidates)
        state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        CERT.atomic_json(state_path, state)
    print(json.dumps({k:v for k,v in state.items() if k != 'configuration'}), flush=True)


if __name__ == '__main__':
    main()
