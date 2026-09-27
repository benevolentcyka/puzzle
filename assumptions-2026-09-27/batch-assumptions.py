"""Batch hash-entry and hash-algorithm candidates across source boundaries.

Uses the same generators as search-assumptions.py, with cached BIP44 parents.
It has separate checkpoints; prototype partial results are not added to totals.
"""
import argparse
import datetime
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'expanded-2026-09-26'))
sys.path.insert(0, str(ROOT / 'bip39-gpu-review/src'))
from wallet_paths_gpu import WalletPathsGPU
import importlib.util
spec = importlib.util.spec_from_file_location('assumptions', HERE / 'search-assumptions.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


def entries(candidates, family):
    for target, md, label in candidates:
        seen = set()
        source = label['source']
        if family == 'hash-entry':
            variants = ((A.historical_raw(text), edit) for text, edit in A.entry_variants(md))
        else:
            variants = A.algorithm_variants(source)
        for entropy, edit in variants:
            if not entropy or entropy in seen:
                continue
            seen.add(entropy)
            yield target, entropy, edit, label


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--family', choices=['hash-entry', 'hash-algorithm'], required=True)
    ap.add_argument('--target', choices=['example', 'chapter', 'both'], default='both')
    ap.add_argument('--indices', default='0,1,2,3,4,5,6')
    ap.add_argument('--batch', type=int, default=16384)
    ap.add_argument('--platform', type=int, default=1)
    ap.add_argument('--limit', type=int)
    args = ap.parse_args()
    indices = [int(i) for i in args.indices.split(',')]
    if not indices or len(set(indices)) != len(indices) or any(i < 0 or i >= 2**31 for i in indices):
        ap.error('Use distinct nonhardened indices')
    if args.batch < 1 or (args.limit is not None and args.limit < 1):
        ap.error('Batch and limit must be positive')
    targets = ['example', 'chapter'] if args.target == 'both' else [args.target]
    candidates = []
    for target in targets:
        data = A.HELPER.canonical_example_candidates() if target == 'example' else A.HELPER.chapter_candidates()
        candidates += [(target, md, label) for md, label in data]
    candidate_hash = hashlib.sha256()
    for target, md, label in candidates:
        candidate_hash.update(target.encode() + b'\0' + label['source'] + b'\0')
    comparisons = A.certify_historical()
    print(f'PASS: {comparisons} historical input/mnemonic fixtures', flush=True)
    from bip39_gpu.gpu import context, pbkdf2_gpu
    from bip39_gpu.gpu.bip32_gpu import hash160_to_p2pkh, base58check_encode
    from bip_utils import Bip32Secp256k1, Base58Decoder
    context._global_context = context.GPUContext(platform_id=args.platform)
    pbkdf2_gpu._pbkdf2_cpu_fallback = A.CERT.die_fallback
    gpu = WalletPathsGPU(context._global_context)
    parent = "m/44'/0'/0'/0"
    certified = gpu.certify([{'parent': parent, 'hardened': False, 'direct': False}])
    target_map = {Base58Decoder.CheckDecode(address)[1:]: address for target in targets for address in A.TARGETS[target]}
    config = {'family': args.family, 'target': args.target, 'indices': indices, 'source_bases': len(candidates),
              'candidate_source_sha256': candidate_hash.hexdigest(), 'prefix_filter': None,
              'mnemonic_language': 'english', 'passphrase': '', 'parent': parent,
              'historical_js_fixtures': comparisons, 'bip32_certified_comparisons': certified,
              'wallet_kernel_sha256': gpu.kernel_sha256, 'gpu_kernel_sha256': A.CERT.gpu_kernel_fingerprint(),
              'code_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), HERE/'search-assumptions.py', HERE/'historical-input.cjs']}}
    tag = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
    dest = HERE / f'batch-{args.family}-{args.target}-{tag}.json'
    state = json.loads(dest.read_bytes()) if dest.exists() else {
        'configuration': config, 'next_rank': 0, 'derived_addresses': 0, 'matches': 0, 'complete': False}
    if state['configuration'] != config:
        raise RuntimeError('Checkpoint configuration differs')
    if state['complete'] or state['matches']:
        print(f'Already finished: {dest.name}', flush=True)
        return
    stream = entries(candidates, args.family)
    # Replay generation, not derivation, to resume the exact ordered stream.
    for _ in itertools.islice(stream, state['next_rank']):
        pass
    initial = state['next_rank']
    begun = time.monotonic()
    print(f'{dest.name}: resuming entropy {initial:,}', flush=True)
    while True:
        count = args.batch if args.limit is None else min(args.batch, args.limit - state['next_rank'] + initial)
        if count <= 0:
            break
        batch = list(itertools.islice(stream, count))
        if not batch:
            state['complete'] = True
            state['entropy_candidates_total'] = state['next_rank']
            break
        words = [A.mnemonic(e) for _, e, _, _ in batch]
        seeds = pbkdf2_gpu.pbkdf2_hmac_sha512_gpu([A.HELPER.normalized_password(w) for w in words], [b'mnemonic']*len(words))
        hashes, keys, pubs = gpu.batch(seeds, parent, indices, False, False)
        sampled = sorted({0, len(batch)//2, len(batch)-1})
        for k in sampled:
            seed = hashlib.pbkdf2_hmac('sha512', words[k].encode(), b'mnemonic', 2048, 64)
            if seed != seeds[k]:
                raise RuntimeError('Sampled PBKDF2 disagreement')
            for j, index in enumerate(indices):
                node = Bip32Secp256k1.FromSeed(seed).DerivePath(f'{parent}/{index}')
                public = node.PublicKey().RawCompressed().ToBytes()
                h = hashlib.new('ripemd160', hashlib.sha256(public).digest()).digest()
                row = k*len(indices)+j
                if hashes[row].tobytes() != h or keys[row].tobytes() != node.PrivateKey().Raw().ToBytes() or pubs[row].tobytes() != public:
                    raise RuntimeError('Sampled private/public/address disagreement')
        for row in range(len(hashes)):
            address = target_map.get(hashes[row].tobytes())
            if address is None:
                continue
            k, j = divmod(row, len(indices))
            target, entropy, edit, label = batch[k]
            if address not in A.TARGETS[target]:
                continue
            seed = hashlib.pbkdf2_hmac('sha512', words[k].encode(), b'mnemonic', 2048, 64)
            path = f'{parent}/{indices[j]}'
            node = Bip32Secp256k1.FromSeed(seed).DerivePath(path)
            public = node.PublicKey().RawCompressed().ToBytes()
            if hash160_to_p2pkh(hashlib.new('ripemd160', hashlib.sha256(public).digest()).digest()) != address:
                raise RuntimeError('Hit failed independent validation')
            witness = HERE / f'FOUND-batch-{args.family}-{target}.txt'
            witness.write_bytes(label['source'])
            A.CERT.atomic_json(witness.with_suffix('.json'), {'address': address, 'path': path, 'entropy': entropy.hex(),
                'mnemonic': words[k], 'private_wif': base58check_encode(b'\x80'+node.PrivateKey().Raw().ToBytes()+b'\x01'),
                'edit': edit, 'source': {k:v for k,v in label.items() if k != 'source'}, 'configuration': config})
            state['matches'] += 1
            A.CERT.atomic_json(dest, state)
            print(f'VERIFIED MATCH saved privately at {witness}', flush=True)
            return
        state['next_rank'] += len(batch)
        state['derived_addresses'] += len(batch)*len(indices)
        state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        A.CERT.atomic_json(dest, state)
        print(f"entropies={state['next_rank']:,} addresses={state['derived_addresses']:,} elapsed={time.monotonic()-begun:.1f}s", flush=True)
    A.CERT.atomic_json(dest, state)
    print(json.dumps({k:v for k,v in state.items() if k != 'configuration'}), flush=True)


if __name__ == '__main__':
    main()
