"""Search independent boundary-letter subsets, beyond the two-letter family.

All four planted groups contain 32 distinct first/last ASCII letters. The
default baseline applies the documented first-lower/last-upper rule. A radius
of 8 tests all subsets of up to eight further toggles (15,033,173 texts); a
radius of 32 covers all 4,294,967,296 subsets. Each checkpoint binds the exact
bytes, positions, radius, indices, and both GPU programs. No MD5 hint filter.
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
sys.path.insert(0, str(HERE))
from mask_md5_gpu import MaskMD5GPU, subset_masks
from sparse_md5_gpu import SparseMD5GPU

GROUPS = [[4,5,6,7], [92,93,94,95], [167,168,169,170], [230,231,232,234]]
TARGETS = ['14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W', '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC']


def load_cert():
    spec = importlib.util.spec_from_file_location('pair_certifier', ROOT / 'gpu-case-pairs.py')
    cert = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cert)
    return cert


def chapter_source(join, start, spaces, baseline, internal_newlines, position_scope='marked'):
    paras = json.loads((ROOT / 'wattpad-paragraphs.json').read_text(encoding='utf8'))
    assert len(paras) == 273
    selected = {p for group in GROUPS for p in group}
    separator = '\n\n' if join == 'lf' else '\r\n\r\n'
    parts, positions, offset = [], [], 0
    for i in range(start, len(paras)):
        p = paras[i].replace('\r\n', '\n').replace('\r', '\n')
        if spaces != 'keep': p = p.replace('\u00a0', ' ')
        if spaces == 'trim': p = p.strip()
        if join == 'crlf' and internal_newlines == 'match': p = p.replace('\n', '\r\n')
        part = bytearray(p.encode('utf8'))
        letters = [j for j, b in enumerate(part) if 65 <= b <= 90 or 97 <= b <= 122]
        if letters and (i in selected or position_scope == 'all-boundaries'):
            first, last = letters[0], letters[-1]
            if baseline == 'ffww' and i in selected:
                part[first] |= 32
                part[last] &= ~32
            positions.extend([offset + first, offset + last])
        parts.append(bytes(part)); offset += len(part) + len(separator)
    source = separator.encode().join(parts)
    positions = sorted(set(positions))
    if position_scope == 'marked': assert len(positions) == 32
    if start == 0 and spaces == 'keep' and baseline == 'ffww' and internal_newlines == 'preserve':
        reference = ROOT / 'bases' / ('four-groups-lflf.txt' if join == 'lf' else 'four-groups-crlfcrlf.txt')
        if source != reference.read_bytes():
            raise RuntimeError('Constructed chapter differs from existing byte-audited baseline')
    return source, positions


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--join', choices=['lf','crlf'], default='lf')
    ap.add_argument('--start-paragraph', type=int, choices=[0,1,3], default=0)
    ap.add_argument('--spaces', choices=['keep','nbsp-space','trim'], default='keep')
    ap.add_argument('--baseline', choices=['ffww','raw'], default='ffww')
    ap.add_argument('--internal-newlines', choices=['preserve','match'], default='preserve')
    ap.add_argument('--positions', choices=['marked','all-boundaries'], default='marked')
    ap.add_argument('--radius', type=int, default=8)
    ap.add_argument('--minimum-edits', type=int, default=0)
    ap.add_argument('--indices', default='0')
    ap.add_argument('--platform', type=int, default=1)
    ap.add_argument('--batch', type=int, default=65536)
    ap.add_argument('--limit', type=int, help='Maximum new candidates this invocation; omission runs to completion')
    args = ap.parse_args()
    indices = [int(i) for i in args.indices.split(',')]
    if not 0 <= args.minimum_edits <= args.radius <= 32: ap.error('Use 0 <= minimum-edits <= radius <= 32')
    if args.positions == 'all-boundaries' and args.radius > 4: ap.error('The whole-chapter sparse family supports radius 0..4')
    if not indices or len(set(indices)) != len(indices) or any(i < 0 or i >= 2**31 for i in indices): ap.error('Use distinct normal address indices')
    if args.batch < 1 or (args.limit is not None and args.limit < 1): ap.error('Batch and limit must be positive')
    cert = load_cert()
    from bip39_gpu.core.mnemonic import BIP39Mnemonic
    from bip39_gpu.gpu import context, pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs, hash160_to_p2pkh
    from bip_utils import Base58Decoder, Bip44, Bip44Coins, Bip44Changes, Bip39SeedGenerator
    context._global_context = context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback = cert.die_fallback
    source, positions = chapter_source(args.join, args.start_paragraph, args.spaces, args.baseline, args.internal_newlines, args.positions)
    md5_class = MaskMD5GPU if args.positions == 'marked' else SparseMD5GPU
    md5 = md5_class(context._global_context, source, positions)
    comparisons = md5.certify()
    for i in {indices[0], indices[-1]}: cert.certify_gpu(i)
    total = sum(math.comb(len(positions), k) for k in range(args.minimum_edits, args.radius + 1))
    configuration = {'join':args.join, 'start_paragraph':args.start_paragraph, 'spaces':args.spaces,
                     'baseline':args.baseline, 'internal_newlines':args.internal_newlines, 'minimum_edits':args.minimum_edits, 'radius':args.radius,
                     'indices':indices, 'positions':positions, 'source_sha256':hashlib.sha256(source).hexdigest(),
                     'md5_kernel_sha256':md5.kernel_sha256, 'gpu_kernel_sha256':cert.gpu_kernel_fingerprint(),
                     'targets':TARGETS, 'entropy':'raw-md5-128', 'language':'english', 'passphrase':'',
                     'path':"m/44'/0'/0'/0/INDEX", 'enumeration':'weight-then-lexicographic-v1'}
    scope_suffix = '' if args.positions == 'marked' else '-all-boundaries'
    if scope_suffix: configuration.update({'positions_scope':args.positions,'enumeration':'sparse-weight-then-lexicographic-v1'})
    state_path = HERE / f'chapter-subsets-{args.join}-{args.internal_newlines}-p{args.start_paragraph}-{args.spaces}-{args.baseline}-r{args.minimum_edits}-{args.radius}-i{"-".join(map(str,indices))}{scope_suffix}.json'
    old = json.loads(state_path.read_text()) if state_path.exists() else None
    if old and old['configuration'] != configuration: raise RuntimeError('Checkpoint configuration differs; refusing an invalid resume')
    rank = old['next_rank'] if old else 0
    stop = min(total, rank + args.limit) if args.limit else total
    target_hashes = {Base58Decoder.CheckDecode(a)[1:]:a for a in TARGETS}
    def cpu_node(seed, index):
        return Bip44.FromSeed(seed, Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    def record(matches=0):
        cert.atomic_json(state_path, {'configuration':configuration, 'candidates_total':total, 'next_rank':rank,
                                     'derived_addresses':rank*len(indices), 'complete':rank==total, 'matches':matches,
                                     'md5_certification_comparisons':comparisons,
                                     'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print(f'{state_path.name}: {rank:,}/{total:,} texts; {len(indices)} indices; {len(positions)} independently selectable letters', flush=True)
    begin = time.perf_counter(); last = begin
    while rank < stop:
        size = min(args.batch, stop-rank)
        masks = (subset_masks(len(positions), args.minimum_edits, args.radius, rank, size) if args.positions == 'marked'
                 else md5.descriptors(args.minimum_edits, args.radius, rank, size))
        entropies = md5.batch(masks)
        sampled = sorted({0, size//2, size-1})
        for k in sampled:
            if hashlib.md5(md5.witness(masks[k])).digest() != entropies[k]: raise RuntimeError('Sampled full-source MD5 mismatch')
        words = [str(BIP39Mnemonic.from_entropy(e)) for e in entropies]
        seeds = pbkdf2_gpu.batch_mnemonic_to_seed_gpu(words)
        for k in sampled:
            if Bip39SeedGenerator(words[k]).Generate() != seeds[k]: raise RuntimeError('Sampled independent seed mismatch')
        for index in indices:
            outputs = batch_seed_to_gpu_outputs(seeds, address_index=index)
            if outputs is None: raise RuntimeError('GPU BIP32 unavailable; refusing fallback')
            hashes = outputs[0]
            for k in sampled:
                if cpu_node(seeds[k], index).PublicKey().ToAddress() != hash160_to_p2pkh(hashes[k]): raise RuntimeError('Sampled independent address mismatch')
            for k, h in enumerate(hashes):
                if h not in target_hashes: continue
                witness = md5.witness(masks[k]); node = cpu_node(seeds[k], index)
                if hashlib.md5(witness).digest() != entropies[k] or node.PublicKey().ToAddress() != target_hashes[h]: raise RuntimeError('Hit failed independent validation')
                dest = HERE / 'FOUND-chapter-subsets.txt'; dest.write_bytes(witness)
                descriptor = int(masks[k]) if args.positions == 'marked' else [int(p) for p in masks[k] if int(p)!=0xffffffff]
                cert.atomic_json(dest.with_suffix('.json'), {'configuration':configuration, 'rank':rank+k, 'mask_or_offsets':descriptor,
                                 'md5':entropies[k].hex(), 'index':index, 'address':target_hashes[h],
                                 'mnemonic':words[k], 'private_wif':node.PrivateKey().ToWif()})
                record(matches=1); print(f'VERIFIED MATCH: {dest}', flush=True); return
        rank += size; record()
        now = time.perf_counter()
        if now-last >= 20 or rank == stop:
            print(f'checked={rank:,}/{total:,}; no match; elapsed={now-begin:.1f}s', flush=True); last = now
    record()
    print('COMPLETE finite family' if rank == total else 'LIMIT reached; checkpoint can resume', flush=True)


if __name__ == '__main__': main()
