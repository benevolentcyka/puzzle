"""Search the solved format example without trusting its published MD5 prefix.

All subsets of paragraph first/last ASCII letters, plus the explicitly named
last letter of 'himself' inside the explanatory paragraph, are derived directly.
The three draft choices target the mismatch between 'himself' and the later
sentence appended to that paragraph. No prefix filter discards candidates.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TARGET = '1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi'
TARGET_HASH160 = bytes.fromhex('09d565074752019721ce68c58548ebc13750d5cc')
JOINS = {'lf': '\n\n', 'crlf': '\r\n\r\n', 'lf1': '\n', 'crlf1': '\r\n',
         'lfspace': '\n \n', 'crlfspace': '\r\n \r\n', 'crcr': '\r\r'}


def atomic_json(path, data):
    temp = path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf8')
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dependency', type=Path, default=ROOT / 'bip39-gpu-review')
    parser.add_argument('--draft', choices=['published', 'removed', 'split'], default='published')
    parser.add_argument('--join', choices=list(JOINS), default='lf')
    parser.add_argument('--index', type=int, default=0)
    parser.add_argument('--indices', help='Comma-separated indices; reuse each BIP39 seed for all of them')
    parser.add_argument('--platform', type=int, default=1)
    parser.add_argument('--batch', type=int, default=32768)
    parser.add_argument('--limit', type=int, default=100000)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    indices = [int(x) for x in args.indices.split(',')] if args.indices else [args.index]
    if not indices or any(i < 0 for i in indices) or len(set(indices)) != len(indices):
        parser.error('indices must be distinct nonnegative integers')
    if args.index < 0 or args.batch <= 0 or args.limit <= 0:
        parser.error('index must be nonnegative; batch and limit positive')
    sys.path.insert(0, str(args.dependency / 'src'))
    spec = importlib.util.spec_from_file_location('case_pair_certifier', ROOT / 'gpu-case-pairs.py')
    cert = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cert)
    from bip39_gpu.core.mnemonic import BIP39Mnemonic
    from bip39_gpu.gpu import context, pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs, hash160_to_p2pkh

    posts = json.loads((ROOT / 'aoi-posts-archive.json').read_text(encoding='utf8'))
    post = next(x for x in posts if x['id'] == 'cleczc')
    question = post['selftext'].split('Question:\n\n', 1)[1].split('\n\nFormat:', 1)[0]
    assert hashlib.md5(question.encode()).hexdigest().startswith('7759227')
    paragraphs = question.split('\n\n')
    extra = ' Even after I explained the method used and the result in detail.'
    assert sum(extra in p for p in paragraphs) == 1
    if args.draft == 'removed':
        paragraphs = [p.replace(extra, '') for p in paragraphs]
    elif args.draft == 'split':
        paragraphs = [piece for p in paragraphs for piece in
                      ([p.replace(extra, ''), extra.strip()] if extra in p else [p])]
    separator = JOINS[args.join]
    source = separator.join(paragraphs).encode('ascii')
    positions = []
    offset = 0
    for p in paragraphs:
        letter_positions = [i for i, c in enumerate(p) if c.isascii() and c.isalpha()]
        positions.extend([offset + letter_positions[0], offset + letter_positions[-1]])
        # This is the named word in the prose, not the later quoted example.
        if 'post outing himself.' in p:
            positions.append(offset + p.index('post outing himself.') + len('post outing himself') - 1)
        offset += len(p) + len(separator)
    positions = sorted(set(positions))
    assert len(positions) == {'published': 21, 'removed': 20, 'split': 22}[args.draft]
    sha = hashlib.sha256(source).hexdigest()
    kernel_sha = cert.gpu_kernel_fingerprint()
    total = 1 << len(positions)
    index_tag = f'index{args.index}' if not args.indices else 'indices' + '-'.join(map(str,indices))
    state_path = HERE / f'example-unfiltered-{args.draft}-{args.join}-{index_tag}.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    if state and (state['source_sha256'] != sha or state['offsets'] != positions or
                  state.get('indices', [state.get('index')]) != indices or state['target'] != TARGET):
        raise RuntimeError('Checkpoint source, offsets, index or target mismatch')
    if state and state.get('gpu_kernel_sha256') != kernel_sha:
        raise RuntimeError('Checkpoint used unverified or different GPU kernels; preserve it and restart.')
    rank = state['next_rank'] if state else 0
    initial_rank = rank
    stop = total if args.all else min(total, rank + args.limit)
    prefixes = state.get('published_prefix_candidates', 0) if state else 0
    assert 0 <= rank <= total
    if rank == total:
        print(f'Already completed {args.draft}/{args.join}/{index_tag}: {total:,} candidates', flush=True)
        return
    pbkdf2_gpu._pbkdf2_cpu_fallback = cert.die_fallback
    context._global_context = context.GPUContext(platform_id=args.platform)
    assert hash160_to_p2pkh(TARGET_HASH160) == TARGET
    for index in indices:
        cert.certify_gpu(index)
    print(f'draft={args.draft} join={args.join} indices={indices} letters={len(positions)} ranks=[{rank:,},{stop:,}) '
          f'GPU={context._global_context.device.name}', flush=True)
    work = bytearray(source)
    previous_mask = 0
    begin = time.perf_counter()
    while rank < stop:
        size = min(args.batch, stop - rank)
        entropies = []
        for r in range(rank, rank + size):
            mask = r ^ (r >> 1)
            changed = previous_mask ^ mask
            while changed:
                bit = changed & -changed
                work[positions[bit.bit_length() - 1]] ^= 32
                changed ^= bit
            previous_mask = mask
            h = hashlib.md5(work).digest()
            entropies.append(h)
            prefixes += h[0] == 0x3c and h[1] >> 4 == 6
        mnemonics = [str(BIP39Mnemonic.from_entropy(h)) for h in entropies]
        seeds = pbkdf2_gpu.batch_mnemonic_to_seed_gpu(mnemonics)
        for index in indices:
            outputs = batch_seed_to_gpu_outputs(seeds, address_index=index)
            if outputs is None:
                raise RuntimeError('GPU BIP32 unavailable; CPU fallback refused')
            hashes, _, _ = outputs
            assert len(hashes) == size
            # Certify candidates throughout the actual search, not just startup vectors.
            for k in sorted({0, size // 2, size - 1}):
                expected, _ = cert.cpu_address(entropies[k], index)
                if hash160_to_p2pkh(hashes[k]) != expected:
                    raise RuntimeError(f'CPU/GPU disagreement at candidate {rank+k}, index {index}')
                witness = bytearray(source)
                m = (rank+k) ^ ((rank+k) >> 1)
                for bit, pos in enumerate(positions):
                    if m & (1 << bit):
                        witness[pos] ^= 32
                assert hashlib.md5(witness).digest() == entropies[k]
            for k, h160 in enumerate(hashes):
                if h160 != TARGET_HASH160:
                    continue
                address, words = cert.cpu_address(entropies[k], index)
                if address != TARGET:
                    raise RuntimeError('Potential match failed independent CPU validation')
                hit_rank = rank+k
                hit_mask = hit_rank ^ (hit_rank >> 1)
                witness = bytearray(source)
                for bit, pos in enumerate(positions):
                    if hit_mask & (1 << bit):
                        witness[pos] ^= 32
                assert hashlib.md5(witness).digest() == entropies[k]
                witness_path = HERE / f'FOUND-example-{args.draft}-{args.join}-index{index}.txt'
                witness_path.write_bytes(witness)
                atomic_json(witness_path.with_suffix('.json'), {
                    'address': address, 'entropy_md5': entropies[k].hex(), 'mnemonic': words,
                    'rank': hit_rank, 'mask': hit_mask, 'index': index,
                    'source_sha256': sha, 'offsets': positions,
                    'published_prefix_matches': entropies[k].hex().startswith('3c6'),
                })
                print(f'VERIFIED MATCH {witness_path}', flush=True)
                return
        rank += size
        elapsed = time.perf_counter() - begin
        atomic_json(state_path, {
            'target': TARGET, 'draft': args.draft, 'join': args.join, 'index': args.index,
            'indices': indices, 'derived_addresses': rank * len(indices),
            'source_sha256': sha, 'offsets': positions, 'next_rank': rank,
            'gpu_kernel_sha256': kernel_sha,
            'candidates_total': total, 'complete': rank == total, 'matches': 0,
            'published_prefix_candidates': prefixes,
            'prefix_filter_used': False, 'last_run_speed': (rank - initial_rank) / elapsed,
            'updated_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        })
        print(f'checked={rank:,}/{total:,} speed={(rank-initial_rank)/elapsed:,.0f}/s; no match', flush=True)
    print('No match in this directly derived interval.', flush=True)


if __name__ == '__main__':
    main()
