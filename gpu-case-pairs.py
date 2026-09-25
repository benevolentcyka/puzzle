"""Resumable two-case-toggle search of an exact Quizchain chapter byte file.

This tests one explicitly bounded hypothesis: MD5 of the entire supplied file,
after toggling exactly two distinct ASCII letters, becomes 128-bit BIP39
entropy; an empty-passphrase BIP44 m/44'/0'/0'/0/INDEX P2PKH address then
equals the current prize address. It does not claim to cover other edits,
paragraph choices, historical text revisions, or derivation paths.

Requires Python 3.12+ with numpy, pyopencl, bip_utils and the locally reviewed
copy of BIP39-GPU in ./bip39-gpu-review/src. Run setup-gpu.ps1 on a fresh
clone to pin and patch it. GPU fallback is disabled here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "bip39-gpu-review" / "src"))

from bip39_gpu.core.mnemonic import BIP39Mnemonic
from bip39_gpu.gpu import context, pbkdf2_gpu
from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs, hash160_to_p2pkh
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Changes, Bip44Coins

TARGET_ADDRESS = "14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W"
TARGET_HASH160 = bytes.fromhex("2bc16867479a8d01179a6452651abe14a65eb61a")
STAGE_ONE_ENTROPY = bytes.fromhex("9dd2efb9bc976c2095bd534d7b8d431c")
STAGE_ONE_ADDRESS = "19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN"


def die_fallback(*_args, **_kwargs):
    raise RuntimeError("OpenCL PBKDF2 fell back to CPU; refusing to continue")


def cpu_address(entropy: bytes, index: int) -> tuple[str, str]:
    mnemonic = str(BIP39Mnemonic.from_entropy(entropy))
    seed = Bip39SeedGenerator(mnemonic).Generate()
    node = (Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
            .Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(index))
    return node.PublicKey().ToAddress(), mnemonic


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def pair_at(rank: int, n: int) -> tuple[int, int]:
    """Lexicographic unranking of (i,j), 0 <= i < j < n."""
    lo, hi = 0, n - 1
    while lo < hi:
        mid = (lo + hi) // 2
        before = mid * (2 * n - mid - 1) // 2
        if before <= rank:
            lo = mid + 1
        else:
            hi = mid
    i = lo - 1
    before = i * (2 * n - i - 1) // 2
    j = i + 1 + (rank - before)
    assert 0 <= i < j < n
    return i, j


def iter_pair_batch(start: int, count: int, n: int):
    i, j = pair_at(start, n)
    for _ in range(count):
        yield i, j
        j += 1
        if j == n:
            i += 1
            j = i + 1


def toggle_ascii(byte: int) -> int:
    return byte ^ 32


def make_batch_entropies(base: bytearray, positions: list[int], start: int, size: int):
    """Hash a batch of pairs while reusing the prefix of each MD5 message."""
    entropies = []
    pair_positions = []
    outer_i = None
    prefix = None
    previous_q = None
    view = memoryview(base)
    for i, j in iter_pair_batch(start, size, len(positions)):
        p, q = positions[i], positions[j]
        if outer_i != i:
            if outer_i is not None:
                old_p = positions[outer_i]
                base[old_p] = toggle_ascii(base[old_p])
            base[p] = toggle_ascii(base[p])
            prefix = hashlib.md5()
            prefix.update(view[:q])
            outer_i = i
        else:
            prefix.update(view[previous_q:q])
        candidate_md5 = prefix.copy()
        candidate_md5.update(bytes((toggle_ascii(base[q]),)))
        candidate_md5.update(view[q+1:])
        entropies.append(candidate_md5.digest())
        previous_q = q
        pair_positions.append((p, q))
    if outer_i is not None:
        old_p = positions[outer_i]
        base[old_p] = toggle_ascii(base[old_p])
    return entropies, pair_positions


def certify_pair_hashing() -> None:
    original = b"aA. Bb!cC dD"
    positions = [i for i,b in enumerate(original) if 65 <= b <= 90 or 97 <= b <= 122]
    total = len(positions) * (len(positions)-1) // 2
    for start in range(total):
        size = min(3, total-start)
        work = bytearray(original)
        got, offsets = make_batch_entropies(work, positions, start, size)
        if work != original:
            raise RuntimeError("Case-pair hashing changed the source bytes")
        for k,(p,q) in enumerate(offsets):
            check = bytearray(original)
            check[p] ^= 32
            check[q] ^= 32
            if hashlib.md5(check).digest() != got[k]:
                raise RuntimeError(f"Incremental MD5 mismatch at pair rank {start+k}")


def certify_gpu(index: int) -> None:
    if hash160_to_p2pkh(TARGET_HASH160) != TARGET_ADDRESS:
        raise RuntimeError("Target address/hash160 constant mismatch")
    entropy = [STAGE_ONE_ENTROPY] + [hashlib.md5(f"case-pairs-cert-{i}".encode()).digest()
                                     for i in range(1, 17)]
    mnemonics = [str(BIP39Mnemonic.from_entropy(e)) for e in entropy]
    seeds = pbkdf2_gpu.batch_mnemonic_to_seed_gpu(mnemonics)
    outputs = batch_seed_to_gpu_outputs(seeds, address_index=index)
    if outputs is None:
        raise RuntimeError("OpenCL BIP32 unavailable; refusing CPU fallback")
    hash160s, private_keys, public_keys = outputs
    if len(hash160s) != len(entropy):
        raise RuntimeError("OpenCL output count mismatch")
    for k in [0, 1, 4, 8, 16]:
        address, _ = cpu_address(entropy[k], index)
        if hash160_to_p2pkh(hash160s[k]) != address:
            raise RuntimeError(f"OpenCL/CPU disagreement on witness {k}")
        if len(private_keys[k]) != 32 or len(public_keys[k]) != 33:
            raise RuntimeError(f"Invalid OpenCL key length on witness {k}")
    if index == 0 and hash160_to_p2pkh(hash160s[0]) != STAGE_ONE_ADDRESS:
        raise RuntimeError("Known solved first-stage address not reproduced")
    print(f"GPU certified with 5 independent CPU comparisons at index {index}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path,
                    default=HERE / "bases" / "four-groups-crlfcrlf.txt")
    ap.add_argument("--index", type=int, default=0,
                    help="BIP44 external address index (default 0)")
    ap.add_argument("--batch", type=int, default=65536,
                    help="OpenCL candidates per batch (default 65536)")
    ap.add_argument("--limit", type=int, default=100000,
                    help="Max candidates in this invocation (default 100000)")
    ap.add_argument("--all", action="store_true",
                    help="Run to the end of this base (may take hours)")
    ap.add_argument("--start", type=int,
                    help="Pair rank to begin at, overriding saved checkpoint")
    ap.add_argument("--checkpoint-every", type=int, default=1)
    ap.add_argument("--platform", type=int, default=1,
                    help="OpenCL platform ID for NVIDIA GPU on this computer")
    args = ap.parse_args()
    if args.index < 0 or args.batch <= 0 or args.limit <= 0 or args.checkpoint_every <= 0:
        ap.error("index >= 0; batch, limit and checkpoint-every must be positive")

    base_path = args.base.resolve(strict=True)
    base = bytearray(base_path.read_bytes())
    positions = [i for i, b in enumerate(base) if 65 <= b <= 90 or 97 <= b <= 122]
    n = len(positions)
    total = n * (n - 1) // 2
    base_sha = hashlib.sha256(base).hexdigest()
    state_path = HERE / f"pair-state-{base_path.stem}-index{args.index}.json"
    state = None
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("base_sha256") != base_sha or state.get("index") != args.index:
            raise RuntimeError(f"Checkpoint does not match the base/index: {state_path}")
    rank = args.start if args.start is not None else (state["next_rank"] if state else 0)
    if not 0 <= rank <= total:
        ap.error("start rank outside pair space")
    stop = total if args.all else min(total, rank + args.limit)
    print(f"base={base_path} sha256={base_sha}", flush=True)
    print(f"letters={n} pairs={total:,} this_run=[{rank:,}, {stop:,})", flush=True)

    # The reviewed dependency normally has a silent CPU fallback. Disable it.
    pbkdf2_gpu._pbkdf2_cpu_fallback = die_fallback
    context._global_context = context.GPUContext(platform_id=args.platform)
    device = context._global_context.device
    print(f"OpenCL device: {device.name}", flush=True)
    certify_pair_hashing()
    certify_gpu(args.index)

    begin = time.perf_counter()
    batches = 0
    while rank < stop:
        size = min(args.batch, stop - rank)
        entropies, pair_positions = make_batch_entropies(base, positions, rank, size)
        mnemonics = [str(BIP39Mnemonic.from_entropy(e)) for e in entropies]
        seeds = pbkdf2_gpu.batch_mnemonic_to_seed_gpu(mnemonics)
        output = batch_seed_to_gpu_outputs(seeds, address_index=args.index)
        if output is None:
            raise RuntimeError("OpenCL BIP32 unavailable; refusing CPU fallback")
        hashes, _, _ = output
        if len(hashes) != size:
            raise RuntimeError("OpenCL output count mismatch")
        for k, h160 in enumerate(hashes):
            if h160 == TARGET_HASH160:
                check, mnemonic = cpu_address(entropies[k], args.index)
                if check != TARGET_ADDRESS:
                    raise RuntimeError("Potential hit disagrees with independent CPU derivation")
                p, q = pair_positions[k]
                witness = bytearray(base)
                witness[p] = toggle_ascii(witness[p])
                witness[q] = toggle_ascii(witness[q])
                witness_path = HERE / f"FOUND-{base_path.stem}-index{args.index}.txt"
                witness_path.write_bytes(witness)
                result_path = HERE / f"FOUND-{base_path.stem}-index{args.index}.json"
                confirmed_seed = Bip39SeedGenerator(mnemonic).Generate()
                confirmed_node = (Bip44.FromSeed(confirmed_seed, Bip44Coins.BITCOIN)
                                  .Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
                                  .AddressIndex(args.index))
                atomic_json(result_path, {
                    "address": check, "entropy_md5": entropies[k].hex(),
                    "mnemonic": mnemonic, "index": args.index,
                    "private_wif": confirmed_node.PrivateKey().ToWif(),
                    "pair_rank": rank + k, "byte_offsets": [p, q],
                    "witness_file": str(witness_path), "base_sha256": base_sha,
                })
                print(f"MATCH: {result_path} / {witness_path}", flush=True)
                return 0
        rank += size
        batches += 1
        if batches % args.checkpoint_every == 0 or rank == stop:
            elapsed = max(time.perf_counter() - begin, 1e-9)
            atomic_json(state_path, {
                "base_file": str(base_path.relative_to(HERE)) if base_path.is_relative_to(HERE) else str(base_path),
                "base_sha256": base_sha,
                "index": args.index, "next_rank": rank,
                "pairs_total": total, "last_run_speed_per_second": round((rank - (args.start if args.start is not None else (state["next_rank"] if state else 0))) / elapsed, 2),
                "updated_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            })
            print(f"checked through {rank:,}/{total:,}; {elapsed:.1f}s; "
                  f"{(rank - (args.start if args.start is not None else (state['next_rank'] if state else 0))) / elapsed:,.0f}/s",
                  flush=True)
    print("No match in this exact bounded interval.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
