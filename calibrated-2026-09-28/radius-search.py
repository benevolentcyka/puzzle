"""Marked-endpoint case radius on the two calibrated bases the 27 shapes omitted.

`rendered`: what a browser copy of the published chapter yields: NBSP as space,
trailing spaces removed at paragraph ends *and before internal line breaks*
(the old `trim` shape kept the four spaces before `<br>`). `promoted`: the draft
with every internal single line break doubled like the paragraph joins. Both
use LF LF joins, raw MD5, English BIP39, empty passphrase, BIP44 index 0.
The 32 FFWW endpoints get the documented baseline plus every subset of up to
RADIUS further toggles, exactly as expanded-2026-09-26/chapter-subsets.py
enumerates them (weight, then lexicographic). No prefix filter. Read-only.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'bip39-gpu-review/src'))
sys.path.insert(0, str(ROOT / 'expanded-2026-09-26'))
from mask_md5_gpu import MaskMD5GPU, subset_masks

GROUPS = [[4, 5, 6, 7], [92, 93, 94, 95], [167, 168, 169, 170], [230, 231, 232, 234]]
TARGETS = ['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W', '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']


def source(base, start):
    paras = json.loads((ROOT / 'wattpad-paragraphs.json').read_text(encoding='utf8'))
    selected = {p for g in GROUPS for p in g}
    parts, positions, offset, sep = [], [], 0, '\n\n'
    for i in range(start, len(paras)):
        p = paras[i].replace(' ', ' ')
        if base == 'rendered':
            p = '\n'.join(line.rstrip(' ') for line in p.split('\n'))
        elif base == 'promoted':
            p = p.replace('\n', sep)
        part = bytearray(p.encode('utf8'))
        letters = [j for j, b in enumerate(part) if 65 <= b <= 90 or 97 <= b <= 122]
        if i in selected:
            part[letters[0]] |= 32
            part[letters[-1]] &= ~32
            positions += [offset + letters[0], offset + letters[-1]]
        parts.append(bytes(part))
        offset += len(part) + len(sep)
    data = sep.encode().join(parts)
    assert len(positions) == 32
    return data, sorted(positions)


def reference(base, start, flips):
    """Independent string-level rebuild: flip the chosen FFWW endpoint letters."""
    paras = json.loads((ROOT / 'wattpad-paragraphs.json').read_text(encoding='utf8'))
    selected = [p for g in GROUPS for p in g]
    ends = []
    for p in sorted(selected):
        idx = [k for k, c in enumerate(paras[p]) if c.isascii() and c.isalpha()]
        ends += [(p, idx[0], 'lower'), (p, idx[-1], 'upper')]
    out = [list(t) for t in paras]
    for n, (p, k, case) in enumerate(ends):
        c = out[p][k].lower() if case == 'lower' else out[p][k].upper()
        if n in flips:
            c = c.swapcase()
        out[p][k] = c
    text = []
    for i in range(start, len(paras)):
        t = ''.join(out[i]).replace(' ', ' ')
        if base == 'rendered':
            t = '\n'.join(line.rstrip(' ') for line in t.split('\n'))
        elif base == 'promoted':
            t = t.replace('\n', '\n\n')
        text.append(t)
    return '\n\n'.join(text).encode('utf8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', choices=['rendered', 'promoted'], required=True)
    ap.add_argument('--start-paragraph', type=int, choices=[0, 1, 3], default=0)
    ap.add_argument('--radius', type=int, default=6)
    ap.add_argument('--platform', type=int, default=1)
    ap.add_argument('--batch', type=int, default=65536)
    args = ap.parse_args()
    if sys.flags.optimize:
        ap.error('Do not use python -O')
    spec = importlib.util.spec_from_file_location('cert', ROOT / 'gpu-case-pairs.py')
    cert = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cert)
    from bip39_gpu.core.mnemonic import BIP39Mnemonic
    from bip39_gpu.gpu import context, pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs, hash160_to_p2pkh
    from bip_utils import Base58Decoder, Bip44, Bip44Coins, Bip44Changes, Bip39SeedGenerator
    context._global_context = context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback = cert.die_fallback
    data, positions = source(args.base, args.start_paragraph)
    # The 32 marked offsets are in paragraph order, so bit n of a mask is endpoint n.
    assert data == reference(args.base, args.start_paragraph, set())
    md5 = MaskMD5GPU(context._global_context, data, positions)
    comparisons = md5.certify()
    cert.certify_gpu(0)
    total = sum(math.comb(32, k) for k in range(args.radius + 1))
    config = dict(family='calibrated-marked-radius-v1', base=args.base, start_paragraph=args.start_paragraph,
                  radius=args.radius, positions=positions, source_sha256=hashlib.sha256(data).hexdigest(),
                  md5_kernel_sha256=md5.kernel_sha256, gpu_kernel_sha256=cert.gpu_kernel_fingerprint(), targets=TARGETS,
                  entropy='raw-md5-128', language='english', passphrase='', path="m/44'/0'/0'/0/0",
                  enumeration='weight-then-lexicographic-v1')
    state_path = HERE / f'radius-{args.base}-p{args.start_paragraph}-r{args.radius}.json'
    old = json.loads(state_path.read_text()) if state_path.exists() else None
    if old and old['configuration'] != config:
        raise RuntimeError('Checkpoint configuration differs; refusing an invalid resume')
    rank = old['next_rank'] if old else 0
    targets = {Base58Decoder.CheckDecode(a)[1:]: a for a in TARGETS}
    node = lambda seed: Bip44.FromSeed(seed, Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)

    def record(match=None):
        cert.atomic_json(state_path, dict(configuration=config, candidates_total=total, next_rank=rank,
            derived_addresses=rank, complete=rank == total, matches=1 if match else 0,
            md5_certification_comparisons=comparisons, updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print(f'{state_path.name}: {rank:,}/{total:,}', flush=True)
    begin = time.perf_counter()
    while rank < total:
        size = min(args.batch, total - rank)
        masks = subset_masks(32, 0, args.radius, rank, size)
        entropies = md5.batch(masks)
        sampled = sorted({0, size // 2, size - 1})
        for k in sampled:
            flips = {n for n in range(32) if int(masks[k]) >> n & 1}
            assert hashlib.md5(reference(args.base, args.start_paragraph, flips)).digest() == entropies[k], 'Independent rebuild mismatch'
        words = [str(BIP39Mnemonic.from_entropy(e)) for e in entropies]
        seeds = pbkdf2_gpu.batch_mnemonic_to_seed_gpu(words)
        for k in sampled:
            assert Bip39SeedGenerator(words[k]).Generate() == seeds[k]
        hashes = batch_seed_to_gpu_outputs(seeds, address_index=0)[0]
        for k in sampled:
            assert node(seeds[k]).PublicKey().ToAddress() == hash160_to_p2pkh(hashes[k])
        for k, h in enumerate(hashes):
            if h in targets:
                witness = md5.witness(masks[k])
                n = node(seeds[k])
                assert hashlib.md5(witness).digest() == entropies[k] and n.PublicKey().ToAddress() == targets[h]
                dest = HERE / f'FOUND-radius-{args.base}-p{args.start_paragraph}.txt'
                dest.write_bytes(witness)
                cert.atomic_json(dest.with_suffix('.json'), dict(configuration=config, rank=rank + k, mask=int(masks[k]),
                    md5=entropies[k].hex(), address=targets[h], mnemonic=words[k], private_wif=n.PrivateKey().ToWif()))
                record(match=True)
                print(f'VERIFIED MATCH: {dest}', flush=True)
                return
        rank += size
        record()
        print(f'{rank:,}/{total:,} rate={rank / (time.perf_counter() - begin):,.0f}/s', flush=True)
    print('COMPLETE, no match in this bounded family', flush=True)


if __name__ == '__main__':
    main()
