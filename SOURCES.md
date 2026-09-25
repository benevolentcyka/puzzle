# Source and data provenance

The scripts and analysis in this repository were written for this investigation.
Saved third-party material is included in this private evidence archive so the
byte-level checks can be repeated. It is not claimed as original work.

| Local files | Source and purpose |
| --- | --- |
| `wattpad-api-*.txt`, `wattpad-paragraphs.json`, `wattpad-paragraph-audit.json`, `wattpad-id-control.json` | [Wattpad chapter 2](https://www.wattpad.com/720888559-second) and [Wattpad text API](https://www.wattpad.com/apiv2/?m=storytext&id=720888559), plus control parts 720895205 and 762380140; preserve paragraph text and IDs for exact-byte testing. |
| `aoi-posts-archive.json`, `aoi-comments-archive.json` | [Arctic Shift public Reddit archive](https://arctic-shift.photon-reddit.com/) listings for author `AoiNakamoto`, paginated to exhaustion on 2026-09-26. |
| `hal-finney-page.html` | [Hal Finney's public Bitcointalk post](https://bitcointalk.org/index.php?topic=155054.0), used to verify the solved first stage. |
| `english.txt` | The [BIP39 English word list](https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt), used by `verifier.cjs`. |
| `patches/bip39-gpu-fixes.patch` | Local fixes against [BIP39-GPU](https://github.com/AlexMelanFromRingo/BIP39-GPU) commit `08f189d3ade6a18e18acc82f18a7bfb576c6e86f` (MIT license). The dependency is fetched by `setup-gpu.ps1` and excluded from this repository. |

The published puzzle and primary author comments are linked individually in
`README.md` and `AUTHOR_AUDIT.md`. A separate public research ledger at
[open-crypto-puzzles](https://github.com/floflo777/open-crypto-puzzles/tree/main/1-big-prizes/aoi-nakamoto-quizchain-0-854btc)
informed search boundaries. Its files are linked rather than copied here.
