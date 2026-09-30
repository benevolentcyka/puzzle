# Mixed formatting after the completed negative runs

<!-- current-completion -->
**Current status, 2026-09-30: COMPLETE, no match.** The authoritative checkpoint
checks all **28,194,048** candidate/address operations, index 0, with 5,163
sampled CPU comparisons and 3,285.234 recorded search seconds.
The 8,962,048 recovery milestone below is historical, not the current remaining
work. The pilot/recovery sections preserve how progress was recovered.
<!-- /current-completion -->

**Unsolved. This is a bounded next hypothesis, not a recovered solution.**
The previous byte-passage search and all 54 broad chapter checkpoints are
complete and negative. This run addresses a different gap in the final chapter:
**combinations of local formatting changes across artifact categories**.

The author's [later format explanation](https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/)
supports keeping the text and changing selected capitalization. The
[discussion](https://www.reddit.com/r/Grycoin/comments/chn8un/real_big_block_discussion/)
explicitly describes two CRLF paragraph breaks. Neither settles the exact
bytes of a copied input. Mixed formatting is our hypothesis about source
serialization, not a newly disclosed author clue.

## Why this is additional coverage

`followup-2026-09-26/chapter-whitespace-gpu.py` exhausts the 13 independent
trailing-space choices with **global** NBSP and internal-break policies.
`chapter-nbsp-gpu.py` exhausts the six independent NBSP choices with **global**
trailing-space and internal-break policies. The delete/promote-break scripts
likewise do not combine all those independent categories. The broad endpoint
case sweeps use whole-text formatting policies.

Their union therefore does not exclude, for example, a single trimmed original
paragraph ending **and** a local NBSP replacement **and** an internal break
changed at another position. This run explicitly combines such deviations.
It can overlap earlier candidates; the count is not a deduplicated entropy
total. A larger count alone is not evidence of a better hypothesis.

## Exact finite scope

The unchanged source is `wattpad-paragraphs.json`. There are 864 baselines:

- All 16 coherent selections of the four FFWW groups. Selected paragraphs
  get a lowercase first ASCII letter and uppercase last ASCII letter.
- Starting paragraph 0, 1, or 3.
- CRLF paragraph joins and CRLF internal breaks; LF throughout; or CRLF
  paragraph joins with internal LF preserved. Joins contain two line breaks.
- All 13 originally trailing ASCII-space runs retained or all removed.
- All six original NBSPs retained, replaced by ASCII space, or removed.

Each local candidate changes **exactly two or three of the 29 observed sites**
from that baseline, involving **at least two categories**:

| Category | Sites | Allowed final representations at a site |
| --- | ---: | --- |
| Original trailing ASCII-space runs | 13 | Exact original run, or empty |
| Original NBSP occurrences | 6 | NBSP, ASCII space, or empty |
| Original internal LF breaks | 10 | LF, CRLF, empty, ASCII space, or the chosen paragraph separator |

Only original artifact sites are changed. No arbitrary prose substitutions,
paragraph reordering, additional case edits or final newline are introduced.
Case changes happen before formatting. Each original trailing-space run is
one site, regardless of how many spaces it contains.

For two changed sites the count per baseline is
`13*12 + 13*40 + 12*40 = 1,156`.
For three changed sites, selecting site counts from the three categories gives
`936 + 3120 + 780 + 2400 + 9360 + 8640 + 6240 = 31,476`.
The script checks these independently against the actual enumeration.

| Phase | Candidate instances |
| --- | ---: |
| Two changed sites across 864 baselines | 998,784 |
| Three changed sites across 864 baselines | 27,195,264 |
| **Total** | **28,194,048** |

It tries the entire two-site phase first, then the three-site phase. Within
each phase, all-four-group, first-three-group and raw capitalization are first;
remaining group masks follow. CRLF throughout is the first newline form.

All candidates use raw MD5 entropy, English BIP39, empty passphrase, and BIP44
`m/44'/0'/0'/0/0`. Both the revised `14zMk...` and original `1EFoj...` addresses
are compared. **No MD5-prefix filter** is used. Index 0 is prioritized by the
author's first-address description and reproduced solved controls. This does
not establish the final derivation setting beyond doubt.

## Run on this machine

```powershell
Set-Location 'C:\Users\boomb\Downloads\puzzle-investigation'
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\joint-format-2026-09-28\resume.py --max-edits 3 --indices 0 --platform 1
```

This is a direct Python invocation; the PowerShell script policy does not
apply. It uses the existing installed dependencies and reviewed GPU code.
Use **`resume.py`**, which runs the unchanged `search.py` with a resilient
checkpoint writer and validated recovery. The original writer failed on a
Windows access-denied error; see the recovery section below.
Run the **same command** after Ctrl+C to resume. Completed batches are saved
atomically; an interrupted batch may repeat. It stops on completion or an
independently confirmed match. A match's exact bytes, metadata, mnemonic and
WIF stay in ignored local `FOUND-*` files. It sends no transactions.

The checkpoint is `joint-format-9e24b2a1e9bbaa8a.json` for the code and settings
in this commit. It binds the source, candidate order, wordlist, helper code,
paths and GPU kernels. A changed configuration gets a different checkpoint;
do not rename a checkpoint to pretend compatible progress. An OS lock prevents
two copies from writing the same checkpoint. The lock file can persist after
exit; the operating system releases the actual lock.

`--limit 100000` checks at most 100,000 **additional** instances and saves the
same checkpoint. `--verify-only` validates enumeration/serialization without
starting wallet computation. `--indices` is configurable, but additional
indices define a different run and repeat the corresponding source generation.
Do not run Python with `-O`; that disables assertions and is explicitly refused.

## Original pilot and runtime (historical)

Two invocations checked **1,310,720** candidate instances/address operations,
with **zero matches**. The second invocation resumed from 131,072, verifying
actual checkpoint continuation. This includes the entire 998,784-candidate
two-site phase and the first 311,936 three-site candidates.

**26,883,328 remain. The whole new family is not exhausted.**

The numbers above describe the original pilot. **The later user run and
recovery advanced the checkpoint to 8,962,048; 19,232,000 remain.**
The family remains incomplete with zero matches. See the recovery section.

The first 131,072 candidates took 8.3 search seconds, about 15,767/s. A longer
1,179,648-candidate continuation took 179.5 seconds, about **6,574/s**, including
the transition into three-site candidates. The longer measurement is the
useful planning estimate: about **68 minutes remaining** at that rate.
Allow roughly **60–90 minutes** on this machine; GPU load and sustained
performance can change that. Startup verification/compilation is extra.
The program prints a fresh rate and remaining-time estimate during execution.
The saved aggregate search time is 187.75 seconds; it excludes startup.

Verification performed:

- 1,734 full-chapter checks of splice/prefix MD5 against a separate
  character-based serializer and direct `hashlib.md5`, covering every baseline
  plus phase/rank boundaries. The two serializers share the documented option
  table; this validates reconstruction, not the historical truth of that table.
- Unique edit-pattern checks and independent combinatorial counts.
- 48 independent private-key/public-key/hash160 comparisons per wallet startup.
- Actual solved Stage One and Grycoin Block 1 addresses detected through the
  matching path on each startup.
- 240 sampled independent mnemonic/seed/key/public-key/hash160 comparisons
  across the two pilot invocations, plus each sampled source MD5 check.
- The restored corrected cryptographic-kernel fingerprint is recorded in the
  checkpoint. Silent PBKDF2 CPU fallback is refused.

If it completes without a match, only this exact joint-format family at the
specified index is excluded. It will not prove that arbitrary case choices,
historical text revisions, other copy artifacts, or converter settings have
been exhausted. Its value is closing a concrete coverage gap; success is not
promised.

## Windows checkpoint failure and recovered progress (historical) (historical) (historical) (historical) (historical) (historical) (historical)

The user's continuation stopped at `tmp.replace(path)` with `WinError 5`.
That is a checkpoint replacement failure, not a completed negative search.
The exact process denying replacement was not identified. A temporary open
file without delete sharing is one reproducible cause; administrator mode or
changing execution policy is not needed for this repair.

The main JSON recorded **8,929,280** checked candidates. Its intact `.json.tmp`
recorded **8,945,664**, one completed batch later. Both matched the exact source,
code/configuration fingerprints, counts and incomplete status. The original
runner writes this temporary state only after checking the full batch.
Recovery validated the records and promoted the newer state under the existing
exclusive checkpoint lock. Both records and a decision report are preserved in
`checkpoint-recovery/`.
The backups preserve the parsed JSON records with LF newlines; the decision
report's SHA256 values identify the original on-disk files, whose writer used
Windows CRLF. This newline normalization does not change candidate identity.

`resume.py --max-edits 3 --indices 0 --platform 1 --limit 16384` then resumed
from **8,945,664**, passed the original serialization and wallet checks, checked
another batch, and saved **8,962,048** successfully. There are **19,232,000**
instances remaining, with zero matches so far. At the user's sustained rate
near 7,000/s, that is roughly 46 minutes; the live estimate will adjust.

`resume.py` changes only startup recovery and checkpoint writing. It explicitly
checks the original search script's SHA256 before loading it and adapts the
writer and locking hooks. The candidate generator, argument parser, crypto
kernels and configuration stay identical, so the checkpoint remains
`joint-format-9e24b2a1e9bbaa8a.json`. The new writer/launcher hashes are recorded
separately as `checkpoint_writer` metadata; they are not hidden changes to
candidate identity. Neither `search.py` nor the shared `gpu-case-pairs.py`
was modified, preserving prior result fingerprints.

The replacement writer:

- Writes to a uniquely named pending file, flushes and calls `fsync`.
- Retries access-denied/sharing errors with bounded backoff for up to 30 seconds.
- Never truncates or deletes the current checkpoint to work around a lock.
- Preserves a pending file if replacement remains unavailable, then stops.
- On the next launch, validates pending saves before recovering the newest one.
  Corrupt/inconsistent files are left untouched; stale saves cannot regress
  progress. A mismatched primary fingerprint is refused.

Eight tests passed, covering a **real Windows no-delete-sharing handle**, injected
transient/persistent permission errors, legacy `.json.tmp` recovery, malformed
and inconsistent states, stale progress, changed code fingerprints, and
conflicting saves at the same rank. Run them independently with:

```powershell
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\joint-format-2026-09-28\test_checkpoint_io.py
```

The repair verification ran one extra batch and stopped; it did not launch an
unattended full search. Use the main command above to continue the remaining work.

For a separate investigator, the repository root now contains
[`CLAUDE-PUZZLE-HANDOFF.md`](../CLAUDE-PUZZLE-HANDOFF.md), with the public prize
context, targets, verified controls, source clues, negative-search bounds,
invalid earlier GPU records, and instructions for a rigorous independent review.
