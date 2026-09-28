# Audit after the unfiltered passage search completed

**Unsolved. No new key or answer was recovered.** The next-run recommendation
in the September 27 report is now exhausted. Do not rerun it as new work.

## Observed completed work

The user's `batch-source-spans-example-2de1bff733ef265a.json` records
27,130,032 distinct-per-base entropy candidates and 189,910,224 address
operations, with zero matches. It uses every byte boundary for a single
contiguous deletion or duplication across 12 example bases, with no MD5-prefix
filter, English/raw MD5, empty passphrase, and BIP44 indices 0–6. The completion
counts and six code fingerprints agree with the current checkout. This is an
observed result, not an assumed negative or a script-policy failure.

The earlier expanded chapter run is now also genuinely complete. All 54
required checkpoint files were read and checked against regenerated chapter
bytes, selected offsets, exact combinatorial totals, both targets and the
corrected MD5/cryptographic kernel fingerprints:

| Completed family | Formats | Address operations |
| --- | ---: | ---: |
| Up to ten toggles at the 32 marked endpoints | 27 | 2,905,043,751 |
| Exactly three toggles at any paragraph endpoint | 27 | 709,943,940 |

These operations overlap. They are not a count of unique wallets. The audit
verifies checkpoint identity and recorded completion, not a replay of every
GPU operation. `verified-expanded-completions.json` pins all 54 result files.
The historical wallet matrix was already completed earlier; its newer timestamp
is not additional coverage.

## Which examples actually validate the method

Stage One is a verified end-to-end positive control: the saved 16-paragraph
source, specified capitalization and LF separators produce MD5
`9dd2efb9bc976c2095bd534d7b8d431c`, and then the funded address
`19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN` at `m/44'/0'/0'/0/0`.
`node verify-stage-one.cjs` passed again during this audit. The independent
author WIF fixture also passed. Grycoin Block 1 is a second positive control.

Grycoin Block 2, the later format example, has a confirmed payout but **no
reconstructed answer-to-address match in this repository**. It must not be
treated as a verified answer fixture or a prerequisite for trusting the two
actual positive controls. Its raw question matches the author's published
**seven-digit prefix**, not a published full MD5 digest. The full 32-digit
digest in the repository is our own computation.

[The solver says Stage One was easy after Block 2](https://www.reddit.com/r/Grycoin/comments/ca6jxv/comment/evvmey8/).
That is direct testimony of useful information flowing between the puzzles.
[Aoi says she does not know the example's claiming step](https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evwv4rm/).
Neither discloses the precise source bytes or establishes a specific tool bug.
The example therefore remains an unresolved separate target, not evidence that
the final chapter necessarily needs a larger text edit.

The live Stage One thread also contains a recent solver's report of extensive
negative searches and a request to puzzleponky. Those counts and the claim that
the chapter was edited were not independently verified. No response giving
the missing method was visible in the inspected thread. We did not contact anyone.

## Bounded stale-input check

`public-wallet-audit.py` tests whether the example or either prize address
could come from reused publicly disclosed text, literal hashes or WIFs.
This is a hypothesis, not evidence that the author reused an input.

The extraction covers 1,121 public records created before the example's
funding block, from the two Aoi archives and the saved puzzleponky comments.
Archived record text can include later edits. It extracts paragraph/line text,
double-quoted spans and solution clauses, with exact and trimmed forms bounded
to 4,096 characters. It tests MD5 and SHA256 entropy, plus literal 32/64-digit
hexadecimal strings, at BIP44 indices 0–20. It also checks both public-key
compression forms of checksum-valid published WIFs. It does not reconstruct
every historical solution/TOMI/link combination.

Result: **8,735 distinct entropy values, 183,435 derived addresses, and 32 direct
address checks from 16 valid published WIFs; no target match.** Both solved
control addresses were detected by this exact matching pipeline. GPU private
keys, public keys and hash160 values passed 189 sampled independent CPU
comparisons in addition to the startup checks. See `public-wallet-result.json`.

The chain audit confirms the example address has exactly one funded output
and one spend. Its funding output is 700,000 sats at transaction
`f11eca9925c7809210796a3c8d95677dfaf0becb4f6df4c74e7261c3011a2e3c`, vout 0.
The expected 77,700,000-satoshi final output remains unspent at the recorded
check. Responses and their URLs are preserved in `chain-audit.json`.

## Decision

**Subsequent follow-up:** after this audit, the user requested another bounded
local run. [The joint-format report](../joint-format-2026-09-28/README.md)
documents a concrete gap between previously separate artifact categories and
the new, only partially executed search. It does not change the completed
negatives here or establish a new author clue. The paragraph below records
the recommendation at the end of the earlier audit.

There is currently no evidence-supported next long sweep recommended here.
The passage-edit family is closed at its documented bounds. Larger case radii
or more arbitrary text alterations would be further guesses, not deductions
from the negative results. Useful new evidence would be an actual 2019 answer
buffer, the example's exact solved MD5 plus converter settings, or a newly
recovered author clue that predicts a specific transformation. None was
recovered in this audit. The puzzle is not thereby proved impossible.
