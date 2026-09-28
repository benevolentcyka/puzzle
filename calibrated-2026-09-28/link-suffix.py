"""Stage-One link suffix on the calibrated chapter bases.

Round 1 and early round 2 answers used "[solution] [link]", the link being the
last 3 (later 7) characters of the previous block's private key; block 29 is a
reproduced long-text example. The final block's post gives no Format line and
calls itself the second stage of a two-stage block. This checks the chapter
answer followed by a separator and the Stage One key (last 3, last 7, or whole
WIF) for all 16 FFWW group masks on every calibrated base in twist-search.py.
Index 0, both targets, no prefix filter, read-only.
"""
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    if sys.flags.optimize:
        raise SystemExit('Do not use python -O')
    twist = module('twist', HERE / 'twist-search.py')
    joint = module('joint', ROOT / 'joint-format-2026-09-28/search.py')
    wallet = joint.Wallet(1, [0])  # also puts the reviewed GPU package on sys.path
    from bip_utils import Base58Decoder, Bip32Secp256k1, Bip39MnemonicGenerator, Bip39SeedGenerator
    from bip39_gpu.gpu.bip32_gpu import base58check_encode
    words = str(Bip39MnemonicGenerator().FromEntropy(bytes.fromhex('9dd2efb9bc976c2095bd534d7b8d431c')))
    node = Bip32Secp256k1.FromSeed(Bip39SeedGenerator(words).Generate('')).DerivePath("m/44'/0'/0'/0/0")
    wif = base58check_encode(b'\x80' + node.PrivateKey().Raw().ToBytes() + b'\x01')
    # Confirm this really is the solved Stage One key before using any part of it.
    pub = node.PublicKey().RawCompressed().ToBytes()
    h160 = hashlib.new('ripemd160', hashlib.sha256(pub).digest()).digest()
    assert h160 == Base58Decoder.CheckDecode('19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN')[1:]
    links = {'last3': wif[-3:], 'last7': wif[-7:], 'wif': wif}
    seps = [' ', '', '\n\n']
    targets = {Base58Decoder.CheckDecode(a)[1:]: a for a in twist.TARGETS}
    items, seen = [], set()
    for bi, base in enumerate(twist.BASES):
        for mask in range(16):
            text = twist.reference(base, (mask, 'both', (), ()))
            for (ln, link), sep in itertools.product(links.items(), seps):
                data = text + (sep + link).encode()
                d = hashlib.md5(data).digest()
                if d not in seen:
                    seen.add(d)
                    items.append((dict(base=bi, mask=mask, link=ln, sep=sep), d))
    entropies = [d for _, d in items]
    w, seeds, out = wallet.derive(entropies, [0])
    wallet.compare(w, seeds, out, [(k, entropies[k]) for k in (0, len(items) // 2, len(items) - 1)], [0])
    hits = []
    for raw, address in targets.items():
        for r in wallet.np.flatnonzero(wallet.np.all(out[0] == wallet.np.frombuffer(raw, dtype=wallet.np.uint8), axis=1)):
            hits.append(dict(items[int(r)][0], address=address))
    result = dict(family='stage-one-link-suffix-v1', candidates=len(items), index=0, targets=twist.TARGETS,
                  links=list(links), separators=seps, bases=len(twist.BASES), group_masks=16, matches=hits)
    if hits:
        (HERE / 'FOUND-link-suffix.json').write_text(json.dumps(dict(result, stage_one_wif=wif), indent=2))
        print('MATCH saved to FOUND-link-suffix.json')
    (HERE / 'link-suffix-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('candidates', 'matches')}))


if __name__ == '__main__':
    main()
