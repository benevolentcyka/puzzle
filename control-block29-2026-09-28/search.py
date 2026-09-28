"""Reproduce solved Quizchain round-1 block 29 as a long-text positive control.

The author posted the answer text as "Copypaste from my draft, exactly same as
used for hashing" (Reddit bc6rkn, archived selftext), then disclosed the
solution: change "voice" in the second sentence to "vOIce". The format was
"[solution] [link]" with one space; the link is the last three characters of
the unpublished block 28 private key. This enumerates all 58**3 Base58 links
under LF/CRLF draft line endings and MD5/SHA-256 entropy, English BIP39, empty
passphrase, m/44'/0'/0'/0/0. Target is the block 29 funding output. Read-only;
no network access and no transactions.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TARGET = '1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P'  # tx b49ebc67...7d77 output 0, 770,000 sats
BASE58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
PARENT = "m/44'/0'/0'/0"
FORMS = [(newline, algorithm) for algorithm in ['md5', 'sha256'] for newline in ['\n', '\r\n']]


def draft():
    posts = json.loads((ROOT / 'aoi-posts-archive.json').read_bytes())
    text = next(p['selftext'] for p in posts if p['id'] == 'bc6rkn')
    start = text.index('hashing:\n\n') + len('hashing:\n\n')
    body = text[start:text.index('\n\nUpdate: Block solved')]
    assert len(body.split()) == 235, 'Author stated the answer has 235 words'
    lines = body.split('\n')
    assert len(lines) == 17 and lines[1] == 'A pleasant female voice.'
    lines[1] = 'A pleasant female vOIce.'
    return lines


def candidate(lines, form, link):
    newline, algorithm = form
    data = (newline.join(lines) + ' ' + link).encode('utf8')
    return data, getattr(hashlib, algorithm)(data).digest()


def load_wallet():
    spec = importlib.util.spec_from_file_location('joint', ROOT / 'joint-format-2026-09-28/search.py')
    joint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(joint)
    return joint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', type=int, default=1)
    parser.add_argument('--batch', type=int, default=16384)
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error('Do not use python -O')
    lines = draft()
    links = [''.join(t) for t in itertools.product(BASE58, repeat=3)]
    ranks = [(f, l) for f in FORMS for l in links]
    print(f'{len(ranks):,} candidates ({len(FORMS)} forms x {len(links):,} links), index 0, target {TARGET}', flush=True)
    joint = load_wallet()
    wallet = joint.Wallet(args.platform, [0])  # runs Stage One / Block 1 positive controls
    from bip_utils import Base58Decoder, Bip32Secp256k1
    from bip39_gpu.gpu.bip32_gpu import base58check_encode
    wanted = wallet.np.frombuffer(Base58Decoder.CheckDecode(TARGET)[1:], dtype=wallet.np.uint8)
    begun = time.monotonic()
    for start in range(0, len(ranks), args.batch):
        chunk = ranks[start:start + args.batch]
        entropies = [candidate(lines, f, l)[1] for f, l in chunk]
        words, seeds, out = wallet.derive(entropies, [0])
        sample = sorted({0, len(chunk) // 2, len(chunk) - 1})
        wallet.compare(words, seeds, out, [(k, entropies[k]) for k in sample], [0])
        for r in wallet.np.flatnonzero(wallet.np.all(out[0] == wanted, axis=1)):
            form, link = chunk[int(r)]
            data, entropy = candidate(lines, form, link)
            seed = hashlib.pbkdf2_hmac('sha512', words[int(r)].encode(), b'mnemonic', 2048, 64)
            node = Bip32Secp256k1.FromSeed(seed).DerivePath(f'{PARENT}/0')
            wif = base58check_encode(b'\x80' + node.PrivateKey().Raw().ToBytes() + b'\x01')
            result = dict(target=TARGET, newline=form[0].encode().hex(), algorithm=form[1], link=link,
                          entropy=entropy.hex(), bytes=len(data), wif_suffix=wif[-3:],
                          block30_link_expected='JRu', cpu_confirmed=True)
            # The old prize was claimed in 2019; the key is still kept out of git.
            (HERE / 'FOUND-block29.json').write_text(json.dumps(dict(result, wif=wif, mnemonic=words[int(r)]), indent=2))
            (HERE / 'block29-result.json').write_text(json.dumps(result, indent=2) + '\n')
            print('MATCH', json.dumps(result), flush=True)
            return
        done = start + len(chunk)
        print(f'{done:,}/{len(ranks):,} rate={done / (time.monotonic() - begun):,.0f}/s cpu_samples={wallet.comparisons}', flush=True)
    print('NO MATCH in this family', flush=True)


if __name__ == '__main__':
    main()
