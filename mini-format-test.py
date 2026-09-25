"""Check the later Grycoin format example as an independent calibration."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "bip39-gpu-review" / "src"))
from bip39_gpu.core.mnemonic import BIP39Mnemonic
from bip39_gpu.gpu import context, pbkdf2_gpu
from bip39_gpu.gpu.bip32_gpu import batch_seed_to_gpu_outputs, hash160_to_p2pkh

TARGET = "1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi"
post = next(x for x in json.loads((HERE / "aoi-posts-archive.json").read_text(encoding="utf8"))
            if x["id"] == "cleczc")
q = post["selftext"].split("Question:\n\n", 1)[1].split("\n\nFormat:", 1)[0]
assert hashlib.md5(q.encode()).hexdigest().startswith("7759227"), "Archive text differs from Aoi's published raw MD5"

def deny_fallback(*args, **kwargs):
    raise RuntimeError("PBKDF2 CPU fallback disabled")

pbkdf2_gpu._pbkdf2_cpu_fallback = deny_fallback
context._global_context = context.GPUContext(platform_id=1)
report = {"published_plain_md5_prefix": "7759227", "verified_lf_plain_md5": hashlib.md5(q.encode()).hexdigest(),
          "target_address": TARGET, "hypotheses": []}
for sep in ["\n\n", "\r\n\r\n"]:
    base = bytearray(sep.join(q.split("\n\n")).encode())
    pos = [i for i,x in enumerate(base) if 65 <= x <= 90 or 97 <= x <= 122]
    candidates = []
    # At most two *arbitrary* ASCII capitalization toggles; the public 3c6
    # filter makes full BIP39 derivation inexpensive.
    for count in [0, 1, 2]:
        if count == 0:
            h = hashlib.md5(base).digest()
            if h.hex().startswith("3c6"):
                candidates.append((h, []))
        elif count == 1:
            for p in pos:
                base[p] ^= 32
                h = hashlib.md5(base).digest()
                base[p] ^= 32
                if h.hex().startswith("3c6"):
                    candidates.append((h, [p]))
        else:
            for i,p in enumerate(pos):
                base[p] ^= 32
                for r in pos[i+1:]:
                    base[r] ^= 32
                    h = hashlib.md5(base).digest()
                    base[r] ^= 32
                    if h.hex().startswith("3c6"):
                        candidates.append((h, [p,r]))
                base[p] ^= 32
    entropies = [x[0] for x in candidates]
    mnemonics = [BIP39Mnemonic.from_entropy(e) for e in entropies]
    seeds = pbkdf2_gpu.batch_mnemonic_to_seed_gpu(mnemonics)
    matched = []
    for index in range(7):
        output = batch_seed_to_gpu_outputs(seeds, address_index=index)
        if output is None:
            raise RuntimeError("GPU BIP32 unavailable")
        for k,h160 in enumerate(output[0]):
            if hash160_to_p2pkh(h160) == TARGET:
                matched.append({"index": index, "offsets": candidates[k][1],
                                "md5": candidates[k][0].hex(), "mnemonic": mnemonics[k]})
    item = {"separator": repr(sep), "plain_md5": hashlib.md5(base).hexdigest(),
            "ascii_letters": len(pos), "prefix_passed": len(candidates), "matches": matched}
    report["hypotheses"].append(item)
    print(item, flush=True)
(HERE / "mini-format-results.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
