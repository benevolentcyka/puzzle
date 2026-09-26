# Expanded Quizchain investigation

**Unsolved. There is no independently verified winning key.** Work in this
checkout uses `C:\Users\boomb\Downloads\puzzle-investigation`. The earlier
`quizchain-investigation` folder remains a reference for prior work.

The user's completed corrected LF pair result excludes exactly two additional
ASCII case toggles on the all-four-groups baseline at BIP44 index 0:
641,697,400 pairs. The encoding extension also finished: 97,758,969 address
operations with at most one wrong example MD5-hint digit. Both were observed
negative results, not assumed completions. Neither excludes other families.

## What the new code searches

`chapter-subsets.py` independently toggles the first and last ASCII letter in
each of the 16 marked paragraphs. Its default baseline lowercases the first
letter and uppercases the last in all four groups. The 32 independent choices
include arbitrary mixtures within each group, rather than only coherent group
flips. No MD5 prefix filter is used. English/raw 128-bit MD5 entropy, empty
passphrase and `m/44'/0'/0'/0/INDEX` are explicit assumptions. Both the current
and superseded escrows are compared.

| Radius | Texts per exact byte shape |
| --- | ---: |
| Up to 6 extra toggles | 1,149,017 |
| Up to 8 | 15,033,173 |
| Up to 10 | 107,594,213 |
| Up to 12 | 462,411,533 |
| All 32 choices | 4,294,967,296 |

`--positions all-boundaries` instead includes every paragraph's first/last
ASCII letter, deduplicating one-letter paragraphs. The full chapter has 544
distinct offsets. Exactly three toggles give **26,683,744** texts. This opens
letters outside the planted groups, which the earlier pair search could only
cover two at a time. Sparse unranking supports three or four edits without
restricting the selected positions to a 64-bit mask.

`historical-wallets.py` checks 672 obvious example answers plus 576 chapter
shapes, all eight historical BIP39 languages, and raw plus ten fixed entropy
settings. It does not trust the example's `3c6` hint. Its 13 paths include the
historical converter's BIP32 default, Bitcoin Core with **hardened address
indices**, blockchain.info/Coinomi/Ledger, MultiBit HD, root addresses and
children, plus BIP44 accounts 0/1 and change chains 0/1. Indices are 0–20 by
default; direct roots count once. This matrix completed **27,785,472** address
operations with no match. The paths come from the saved official
[2019 converter source](https://github.com/iancoleman/bip39/blob/45e40c288fe0d6cfba2c57a68f421eeb34d41385/src/js/index.js#L2857);
the additional checkbox/account variants are hypotheses, not known settings.

## Run the larger search locally

On this machine, from PowerShell:

```powershell
Set-Location 'C:\Users\boomb\Downloads\puzzle-investigation'
.\run-expanded-search.ps1 -Python 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' -Radius 10 -Shapes Broad -WholeChapterEdits 3
```

This runs the wallet matrix, then boundary triples and marked-letter subsets
for each shape. Broad means three starting paragraphs (0, 1, 3), three space
policies (retain, NBSP to ordinary spaces, NBSP to spaces plus paragraph trim),
and three newline forms (CRLF paragraph joins with internal LF retained, LF
throughout, CRLF throughout). Thus the marked-letter radius-10 component alone
has **2,905,043,751** operations across 27 shapes at index 0. Triples add another
large family. These are overlapping operations; this is a long GPU run.

Start with `-Shapes Focused` for only the three newline forms and the full,
untrimmed chapter. Use `-SkipWallets` after reviewing the completed matrix.
`-Indices '0,1,2,3,4,5,6'` extends the chapter searches to more addresses and
multiplies their derivation work. The wallet matrix retains its own default
0–20 index range. `-WholeChapterEdits 4` switches to exact boundary quadruples;
`-Radius 32` covers all marked-letter subsets for every selected shape.

To resume only the full-chapter CRLF triples:

```powershell
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\expanded-2026-09-26\chapter-subsets.py --join crlf --positions all-boundaries --minimum-edits 3 --radius 3
```

Every completed batch saves an atomic checkpoint. Rerun the same command to
resume. Direct Python commands accept `--limit` for a bounded invocation.
Checkpoints refuse changes to bytes, offsets, settings or kernel fingerprints.
Use `setup-gpu.ps1` first on a fresh machine; the pinned dependency and GPU
carry repair are required. GPU fallback is disabled.

A match is independently checked on CPU and saves exact source bytes,
mnemonic, path and WIF under ignored `FOUND-*` files. The PowerShell driver
stops when such a witness exists. Result records never publish winning key
material.

## Verification and result records

The main new runs completed with no match:

| Completed family | Address operations |
| --- | ---: |
| All marked-letter subsets through radius 8, full original-space chapter, three newline forms, index 0 | 45,099,519 |
| Exactly three edits among all 544 paragraph-boundary letters, CRLF paragraph joins/internal LF, index 0 | 26,683,744 |
| Historical wallet matrix, both source families | 27,785,472 |

These main rows total **99,568,735** overlapping address operations. The ledger
also includes the smaller radius-6 run and driver smoke checks; its complete
total is **100,719,387** operations across 12 records. Higher radii, all marked
subsets and the Broad text formats are supported, not claimed exhausted.

`ledger.json` lists actual complete and incomplete runs. Rebuild it with
`node .\expanded-2026-09-26\refresh-ledger.cjs`. It checks the repaired GPU
fingerprint and count identities; it rejects potential hits for review. The
older 36 complete follow-up reports remain in
`followup-2026-09-26/post-pair-ledger.json` (278,101,729 address operations).
Do not add these counts as though they were disjoint or proof of exhaustion.

Before real searches, the new code passed:

- 8,804 subset comparisons against `itertools`, 87 independent inverse checks
  at 32/40/63-position ranks, and 291 `hashlib` MD5 comparisons.
- 6,267 sparse-subset comparisons against `itertools`, 209 independent inverse
  checks including ranks above 32 bits, and 309 `hashlib` MD5 comparisons.
- 588 independent private-key/public-key/hash160 comparisons against
  `bip_utils` across every path, including hardened and maximum normal indices.
- 192 official multilingual mnemonic/seed vectors. Actual batches also compare
  CPU and GPU MD5/seed/address outputs; wallet batches check private and public
  keys as well as hash160.
- 18 exact-byte comparisons of the heading/space/newline builder against the
  earlier independently implemented 576-shape chapter generator. The driver
  completed live smoke runs through both its marked and sparse branches.

The underlying carry repair already passed 65,541 field-arithmetic and 8,192
full BIP44 comparisons. Invalid earlier GPU snapshots are not negative evidence.

## Primary-source rechecks and remaining gaps

`source-recheck.json` records a fresh read of the live Wattpad API: all 273
paragraph values equal the search source, and the response equals the earlier
live copy. Mempool and Blockstream independently report the 77,700,000-satoshi
funding output unspent. This confirms the current stored text, not the exact
buffer the author hashed in 2019.

The saved account audit contains 202 posts and 864 comments returned by Arctic
Shift. Fresh archive queries after 2019-08-04 returned zero posts/comments.
Deleted or unarchived records remain possible; this is not a claim to have all
material the account ever published. See `../AUTHOR_AUDIT.md` and
`../followup-2026-09-26/research/SOLVER_SOURCE_AUDIT.md`.

The public [solver app](https://rbbpuzzle.up.railway.app) is reachable by a
direct read even though the web tool could not open it. Its hardcoded Stage
One text has the same confirmed MD5, and its GET self-test reproduces Stage
One and the author's WIF calibration. No candidate or winning secret was
submitted to that service. It does not reveal the missing solved-example
buffer or a Stage Two answer.

The solved example still fails to reproduce in the tested families. Its exact
successful bytes and the solver's method remain valuable calibration gaps.
The larger search tests additional concrete hypotheses; it cannot guarantee
the puzzle will yield a match.
