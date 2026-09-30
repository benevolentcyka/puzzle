# Documented source alternatives, 2026-09-30

**UNSOLVED.** The complete source-variant run checked **3,149,568** entropies
and **22,046,976** addresses, indices 0–6, no prefix filter, zero matches.
`source-variants-7c2afdfd24a61177.json` is authoritative; its measured
search time is 317.782 seconds and it records 8,085 sampled CPU wallet
comparisons. Candidate overlap with other runs is expected.

## Why these are different candidates

The [original Finney post](https://bitcointalk.org/index.php?topic=155054.0)
spells a word at the end of its paragraph 4 as `facinating`; final chapter
paragraph 233 spells it `fascinating`. That is a content difference,
which case-only sweeps do not exclude.

Comparison with the author's saved public
[Second Life](https://www.wattpad.com/720889517) and
[THOMAS and SATOSHI](https://www.wattpad.com/757574334) parts identified:

| Final paragraph, zero based | Earlier source paragraph | Difference |
| --- | --- | --- |
| 15 | Second Life 5 | Elapsed-years wording |
| 18 | Second Life 8 | Ranking and timing wording |
| 24 | Second Life 13 | Ordinal |
| 191 | THOMAS 10 | Data versus information wording |
| 193 | THOMAS 12 | Name versus word |
| 203 | THOMAS 22 | Additional phrase |
| 182, 195, 199 | THOMAS 0, 14, 18 | Earlier whitespace/boundaries |
| 233 | Finney 4 | Spelling difference |
| 230, 234 | Finney 1, 5 | Outer quotation delimiters |

These do not prove that any earlier paragraph belonged to the hashed final
buffer. They supply actual, testable alternatives rather than arbitrary
spelling guesses.

The run tries all **4,095 nonempty subsets of 12 changes**, plus six coherent
whole-section alternatives: either or both earlier sections, with/without the
Finney spelling. It uses 768 bases: 16 coherent FFWW group selections × starts
0/1/3 × eight serializations × optional final LF. Exact forms and source
fingerprints are in the checkpoint. Case changes follow substitutions, so
replacement paragraphs keep their selected endpoint transformation.

The serializer was checked by an independent character rebuild for every
local subset on a calibrated draft base. Every wallet batch was sampled on CPU
and matched to independently generated mnemonic, seed, private/public key and
hash160. Actual solved Stage One and Grycoin Block 1 passed on startup.
A match would require a full address comparison and CPU confirmation.

## Reproduce

```powershell
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\source-variants-2026-09-30\search.py
```

The existing complete checkpoint returns without repeating the family.
A fresh clone needs the two ignored source HTML files: use
`fetch-sources.py`, which verifies them against the committed manifest.
The prototype `source-variants-e92eaa4a6a257540.json` checked 65,536
instances before a tuple/list resume mismatch was corrected. It remains local,
superseded by the complete run; its operations are not additional coverage.

## Example counter audit

The completed FFWW example ≤3 checkpoint reports rank 285,846,394 but
`derived=285,835,264`. Inspection showed that the final `flush()`
derives/checks the tail, then fails to update that counter. We did not rewrite
the historical record. `recheck-example-tail.py` independently unranked
and replayed ranks **[285835264, 285846394)**: **11,130** candidates, index 0,
all three public targets, no match. Its proof/result is
`example-tail-recheck.json`. Only the FFWW baseline has a completed
unfiltered ≤3 example search; raw, non-ITASM and author baselines have ≤2.
