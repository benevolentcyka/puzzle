"""Certify and time the local OpenCL candidate library before any GPU search."""
import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here / "bip39-gpu-review" / "src"))

from bip39_gpu.gpu import context
from bip39_gpu.core.mnemonic import BIP39Mnemonic
from bip39_gpu.gpu import pbkdf2_gpu
from bip39_gpu.gpu.pbkdf2_gpu import batch_mnemonic_to_seed_gpu
from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs, hash160_to_p2pkh
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('count', nargs='?', type=int, default=64)
parser.add_argument('--platform', type=int, default=1)
args = parser.parse_args()
context._global_context = context.GPUContext(platform_id=args.platform)
count = args.count
if count < 2:
    raise ValueError('At least two candidates are required for the regression vectors')
entropies = [hashlib.md5(f"gpu-probe-{i}".encode()).digest() for i in range(count)]
entropies[0] = bytes.fromhex("9dd2efb9bc976c2095bd534d7b8d431c")
entropies[1] = bytes.fromhex("bd6509467d92b47897f5b95558b79873")
mnemonics = [BIP39Mnemonic.from_entropy(e) for e in entropies]

def refuse_cpu_fallback(*args, **kwargs):
    raise RuntimeError('GPU probe fell back to CPU')
pbkdf2_gpu._pbkdf2_cpu_fallback = refuse_cpu_fallback
t = time.perf_counter()
seeds = batch_mnemonic_to_seed_gpu(mnemonics)
seed_seconds = time.perf_counter() - t
print(f"seeds {count} in {seed_seconds:.3f}s", flush=True)
t = time.perf_counter()
output = batch_seed_to_gpu_outputs(seeds, address_index=0)
if output is None:
    raise RuntimeError('GPU BIP32 unavailable; refusing CPU fallback')
addresses = [hash160_to_p2pkh(h) for h in output[0]]
address_seconds = time.perf_counter() - t
print(f"addresses {count} in {address_seconds:.3f}s", flush=True)
for i in range(count):
    mnemonic = str(Bip39MnemonicGenerator().FromEntropy(entropies[i]))
    seed = Bip39SeedGenerator(mnemonic).Generate()
    ref = (Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
        .Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(0).PublicKey().ToAddress())
    if seeds[i] != seed or addresses[i] != ref:
        raise RuntimeError(f"GPU mismatch i={i}: seed {seeds[i]==seed}, addr {addresses[i]} vs {ref}")
if addresses[0] != "19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN":
    raise RuntimeError("Known solved address not reproduced")
print(f"PASS {count} candidates, {count} independent CPU cross-checks", flush=True)
