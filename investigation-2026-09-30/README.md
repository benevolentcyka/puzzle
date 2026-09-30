# Quizchain investigation, 2026-09-30

**UNSOLVED. No verified final answer or winning key recovered.**
This pass audited the supplied exhaustion inventory, checked actual source
differences, and tested additional finite families. All work is in
`C:\Users\boomb\Downloads\puzzle-investigation`. No external messages
or transactions were sent.

## Actual progress

Snapshot: 2026-09-30T09:46:13.806126+00:00. Per-directory checkpoints carry exact configuration,
code/source/kernel identity, CPU verification counts and timestamps.

| Family | Checked / total candidate operations | Address operations | Result |
| --- | ---: | ---: | --- |
| Documented earlier wording and quote variants | 3,149,568 / 3,149,568 | 22,046,976 | COMPLETE, no match |
| One ASCII deletion or adjacent duplication, six chapter bases, indices 0–6 | 547,508 / 547,508 | 3,832,556 | COMPLETE, no match |
| One ASCII edit, all four operations, six chapter bases, index 0 | 53,715,176 / 53,715,176 | 53,715,176 | COMPLETE, no match |
| Independent nearby initials, indices 0–6 | 196,608 / 196,608 | 1,376,256 | COMPLETE, no match |
| Every subset of 16 marked paragraph pairs, indices 0–6 | 3,145,728 / 3,145,728 | 22,020,096 | COMPLETE, no match |
| Unusual capitals with voice/title motifs, indices 0–6 | 524,288 / 524,288 | 3,670,016 | COMPLETE, no match |
| Unusual capitals combined with nearby initials, index 0 | 25,165,824 / 25,165,824 | 25,165,824 | COMPLETE, no match |
| Independent nearby first AND last endpoints, index 0 | 50,331,648 / 50,331,648 | 50,331,648 | COMPLETE, no match |

Counts overlap heavily; they are not a globally unique address count.
The superseded source prototype and slower single-edit pilot are not added.
Historical invalid GPU checkpoints remain excluded.

## Findings that change the next search

- The original Finney quote has `facinating`; chapter paragraph 233 has
  `fascinating`. Earlier public story parts also contain six wording and
  three whitespace differences. The documented source family checks every
  subset of these changes plus quote delimiters and complete earlier sections.
- A radius cutoff on 32 FFWW endpoints does not exhaust all paired selections
  of the 16 paragraphs. Likewise, extra nearby paragraphs flipped at both ends
  do not exhaust independently selected initials/ends. These are distinct
  coverage gaps even if most operations overlap older searches.
- `ppM`, `VIrgin`, `BItcoin` are conspicuous interior capitals.
  Correcting all three requires three arbitrary interior changes, outside the
  completed two-letter sweeps. The new motif and combined-initial tests do not
  assume they are mistakes; they try every independent selection.
- The example's completed FFWW ≤3 checkpoint has a stale `derived` counter.
  Code inspection found the final flush is checked but not counted. A separate
  replay of the 11,130-tail-candidate interval found no match. The original
  checkpoint was preserved.

## Corrections to the old inventory

- Positive controls establish the derivation on those examples, not an
  immutable guarantee about the final buffer/settings.
- Block 29's reproduced draft has no NBSPs. It establishes LF/draft bytes on
  that block, not NBSP→space. Evidence for double spaces comes separately from
  the author's public Abstract reposts and chapter HTML.
- The example is outside three case changes only from the FFWW baseline.
  The other three unfiltered baselines have completed ≤2 searches.
- The mixed-format checkpoint is now **complete: 28,194,048**, zero matches.
  Old 8,962,048 progress notes are historical.
- Historical `FOUND-block29.json` is present and ignored. No `FOUND`
  file matches either final prize target.
- A current Wattpad modification timestamp and a zero-result CDX query do not
  certify the exact July 2019 hash buffer or prove all historical copies absent.

## Next local run

The nearby-endpoint family now actually completed all 50,331,648 candidates,
with zero matches. Its former recommendation is retired. See
[the subsequent combined-layout investigation](../different-approach-2026-09-30/README.md)
for the next tested command and actual coverage.

## Resume and publication validation

The recommended run demonstrably resumed from 262,144 to 278,528. New
checkpoint-fingerprinted runner sources are stored byte-for-byte through
per-directory Git attributes; newline normalization would otherwise alter
some recorded script hashes. `verify-publication.py` checks the saved
source identities and compares staged Python/OpenCL blobs with the exact
working files used by the jobs. Its recorded result is
`reproducibility-check.json`.

## Current chain evidence

The read-only mempool.space responses in
[../source-variants-2026-09-30/chain-recheck.json](../source-variants-2026-09-30/chain-recheck.json)
record 77,700,000 sats unspent at 2026-09-30 04:14:35 UTC, including
`outspend/1: spent=false`. This is an observed chain snapshot.
