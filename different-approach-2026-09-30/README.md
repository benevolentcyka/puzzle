# A different approach after the nearby-endpoint negative

**UNSOLVED. No final answer or winning key recovered.** Snapshot: 2026-09-30T09:46:13.992341+00:00.
The user's nearby first/last run actually completed all **50,331,648** candidates,
with zero matches. It is no longer the recommended next run.

## What was reconsidered

The author says the final block preserves the long text and changes selected
letter cases. The strongest selection remains the four planted FFWW/STNM
groups, calibrated by the solved Stage One. Separately, the final chapter
consists of three distinct sections. Formatting choices applied to an entire
source section can change many sites simultaneously. The earlier uniform-policy
searches and two/three-site edits do not exhaust these mixed-section layouts.

Paragraph indices in this report are zero-based.
The chapter explicitly combines an `I` with `STNM` (paragraphs 237–238).
The nearby `I` paragraphs are 3, 91, 164, 165, 166, 233. Selecting their
initials had already been searched on global serializer bases; the new work
crosses those selections with independently formatted sections. This is a
clue-based hypothesis, not a claim that these are the intended extra letters.

The claimed Grycoin Block 2 example remains a useful calibration target.
Its published raw-question prefix `7759227` reproduces, but its claim buffer
does not. Its reference to a paragraph ending in `himself` conflicts with
the following sentence in that paragraph. Prior removed/split-sentence and
case-only searches already address that mismatch; it is not a newly found clue.
The new example runner combines case choices AND clipboard defects together.

## Actual new results

| Family | Text operations checked / total | Address operations | Status |
| --- | ---: | ---: | --- |
| Chapter: independent formatting in three sections, voice retained/vOIce | 3,919,104 / 3,919,104 | 27,433,728 | COMPLETE, 0 matches |
| Chapter: I-STNM signatures first,nearest,all, group masks 15,7,0,1,2,3,4,5,6,8,9,10,11,12,13,14 | 11,757,312 / 11,757,312 | 82,301,184 | COMPLETE, 0 matches |
| Chapter: I-STNM signatures 60 remaining selections, group masks 15,7 | 65,536 / 29,393,280 | 458,752 | PARTIAL, 0 matches |
| Example: boundaries, 1 defect(s), independent case choices, prefix 3c6 | 264,241,152 / 264,241,152 | 450,051 | COMPLETE, 0 matches |

Counts are operations, with overlap; do not sum them as unique wallets.
For the example, `3c6` is an explicit MD5 filter. Only surviving digests
are derived. The chapter runs have **no prefix filter** and check both final
escrows at compressed BIP44 indices 0–6, raw MD5, English BIP39 and empty
passphrase. The two hashes/settings are working hypotheses for the final.

## Best next local run

```powershell
Set-Location 'C:\Users\boomb\Downloads\puzzle-investigation'
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\different-approach-2026-09-30\chapter-signatures.py --i-styles remaining --group-masks 15,7 --platform 1
```

This searches the other **60 nonempty subsets of the six nearby I initials**
with the two strongest FFWW interpretations: all four groups (`15`),
or the first three excluding the quoted Stage One group (`7`).
Each is crossed with independent section policies and `voice`/`vOIce`.
Total: **29,393,280 entropy candidates / 205,752,960 address operations**.
The exact command has checked **65,536 / 29,393,280** candidates, with zero matches.
It successfully resumed from rank 32,768 to 65,536; **29,327,744 remain**.
It reuses the corrected GPU dependency already installed on this machine.
It invokes Python directly, so the PowerShell execution-policy error does not apply.

Budget approximately **45–90 minutes** on the measured RTX 4060 laptop, with
more time under load. Startup builds and verifies its source/layout plan before
GPU progress appears. The same command resumes its own fingerprinted checkpoint.
For a short initial run, append `--limit 32768`; remove it to continue.

An optional broader version removes `--group-masks 15,7`, keeping all
16 group selections: **235,146,240 entropy candidates / 1,646,023,680 addresses**,
roughly **5–10 hours** here. The previous default first/nearest/all I signatures
are excluded by `--i-styles remaining`. This still does not exhaust arbitrary
source bytes, case patterns or derivation settings.

## Exact formatting choices

Sections are paragraphs 0–86, 87–161 and 162–272. Each independently chooses:

- Embedded line breaks: retain LF, match the global platform, promote to a
  paragraph separator, replace with a space, or remove.
- Paragraph/pre-embedded-break spaces: keep or trim.
- NBSPs: keep, replace with ordinary space, or remove. Section I has none.
- Section I only: keep `voice` or use the previously solved `vOIce`.

The global paragraph separator stays uniformly LF LF or CRLF CRLF. Starts
0/1/3 and no terminal newline / LF / CRLF are included. Byte-identical section
options are deduplicated before enumeration. Neither paragraph words nor
their ordering are guessed. The returned exact policy is sufficient to
reconstruct a candidate.

## All-source comparison and current primary evidence

`source-audit.py` checks the SHA256 and byte count of all 33 saved Wattpad
parts, including the current chapter, then compares the other 32 parts and
the author's 202 archived posts / 864 comments. It compared
**2,983 distinct normalized paragraphs**
with a declared similarity threshold 0.88. All additional close matches were
already tested earlier wordings or a Reddit `Hint two:` preface to an
otherwise exact quote. It found no additional close draft wording. Whitespace
is normalized for this audit; it does not exclude differently formatted or
more heavily rewritten historical text.

`public-recheck.json` records a fresh read-only snapshot at 2026-09-30T09:13:20.401238+00:00:
the revised funding output is unspent, with **77,700,000 sats**. A separate
Arctic Shift query after August 4 returned the already known closing post
and zero later comments. Provider results do not prove that deleted or
unarchived material never existed.

Primary references:

- [Final puzzle and revision](https://www.reddit.com/r/Grycoin/comments/cgkpbb/777_mbtc_quizchain_last_block/)
- [Paragraph-separator clarification](https://www.reddit.com/r/Grycoin/comments/chn8un/real_big_block_discussion/)
- [Claimed format example](https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/)
- [Chapter](https://www.wattpad.com/720888559-second)

## Verification and reproducibility

Every GPU run reproduces the Stage One and Grycoin Block 1 positive controls.
New chapter serializers are independently rebuilt from the paragraph strings,
checked against `hashlib.md5`, and calibrated byte-for-byte to the saved
all-four NBSP-to-space baseline. Actual entropy, mnemonic, PBKDF2 seed,
BIP32 private/public key and hash160 samples are compared with CPU calculations
in every batch. Every example-filter survivor is checked with CPU MD5.
Every match requires CPU reconstruction before its private witness is saved.

The section runner's first 32,768-candidate pilot uncovered a tuple/list
checkpoint-identity issue. Its negative samples remain valid but are excluded
from totals. The corrected runner successfully resumed 8,192 candidates into
the completed family. The signature runner also resumed successfully after
its 16,384-candidate pilot. Exact sources, input, kernels and candidate plan
are fingerprinted. Git stores these new Python files byte-for-byte.

Checkpoint files and `results.json` carry real progress. The static
`chapter-signatures-plan-*.json` stores the full plan once, keeping each
atomic progress write small. Private `FOUND-*` files remain ignored.
