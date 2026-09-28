# After assuming the expanded search is negative

The puzzle remains unsolved. The user's instruction to consider the earlier
run exhausted is a planning assumption; it does not change that run's saved
completion flags. This work uses the existing puzzle checkout only.

## Change of approach

The 2019 Grycoin Block 2 example was claimed, but its funded address still
does not reproduce from the obvious answer. Its unmodified question does
reproduce the author's `7759227` MD5 hint. That makes it a useful smaller
target for testing assumptions shared by the full-chapter searches.

The example describes changing the end of `himself`, although another
sentence follows it in the published paragraph. Removing or separating that
sentence was tested earlier. This pass tests longer copied spans, independent
of capitalization radius, and errors between hashing and entering entropy.
These are hypotheses, not proof that the author made any particular mistake.

## Completed tests

All use English mnemonics, empty passphrase, compressed P2PKH, and BIP44
`m/44'/0'/0'/0/i`, indices 0–6. The chapter checks both prize addresses;
the example checks `1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi`.

| Family | Scope | Address checks | Result |
| --- | --- | ---: | --- |
| Hash-entry errors | 672 canonical example buffers and 576 chapter buffers; one substituted, missing, inserted or transposed hex digit; clipped input; double paste; reversed hex/bytes | 8,773,310 | No match |
| Hash algorithms | The same 1,248 buffers; full MD5, SHA-1/224/256/384/512 and RIPEMD-160; documented SHA-384/512 truncations; second hashes of MD5 bytes or hex | 314,496 | No match |
| Example source spans, with hint | 4,605,540 attempted deletions/duplications between token boundaries and linked-case variants over 12 bases; 919 distinct-per-base MD5s survive `3c6` | 6,433 | No match |
| Example source spans, **without hint** | The same token-boundary passage edits; 3,677,012 distinct-per-base MD5s | 25,739,084 | No match |
| Coherent editor transformations, without hint | 1,248 buffers; smart quotes/apostrophes/ellipsis, UTF-8/16, escaped and HTML text, global case or named-word replacements | 1,060,416 | No match |
| Mixed newline bytes, without hint | All 262,144 independent LF/CRLF choices at the 18 newline bytes, on six example bases | 11,010,048 | No match |
| Paragraph and quoted-token letter endpoints, LF | All 4,294,967,296 subsets of 32 offsets; 1,048,126 `3c6` survivors | 7,336,882 | No match |
| Paragraph and quoted-token letter endpoints, CRLF | All 4,294,967,296 subsets of 32 offsets; 1,048,883 `3c6` survivors | 7,342,181 | No match |
| Sentence endpoints, LF | All 1,073,741,824 subsets of 30 offsets; 262,090 `3c6` survivors | 1,834,630 | No match |
| Sentence endpoints, CRLF | All 1,073,741,824 subsets of 30 offsets; 262,407 `3c6` survivors | 1,836,849 | No match |
| Sentence drafts, without hint | All 32,767 nonempty sentence-retention subsets across six capitalization bases and LF/CRLF; 393,204 operations | 2,752,428 | No match |
| Chapter clipping, without hint | Every prefix/suffix of six exact-byte bases, plus simultaneous removal of 1–256 bytes from each end; 941,946 distinct-per-base MD5s | 6,593,622 | No match |
| Example byte-position passage edits, with hint | 29,148,216 attempted deletions/duplications and linked-case edits over 12 bases; 6,770 distinct-per-base `3c6` survivors | 47,390 | No match |

The first two families do **not** filter on the example's MD5 prefix. Only the
explicitly hint-filtered source-span row and the case-mask rows use that prefix,
so those rows cannot exclude candidates with a different prefix.
Counts overlap prior searches and each other; they are operations, not a
unique-address total or an exhaustive search of all puzzle interpretations.

The quoted-letter runs add eleven offsets inside the quoted instructions
to the previous 21 paragraph/explicit-word offsets. It checks all combinations
of the resulting 32 offsets, including more than three simultaneous internal
edits. Their `3c6` filter remains an assumption. Both joins completed.
The GPU prefix filter passed 24,738 independent MD5/filter comparisons and
checks **every** surviving digest against CPU hashlib before wallet derivation.
The three tested ranges include the top of the 32-bit mask space.

`structural-search.py` separately tests all 30 sentence-endpoint case choices
and every nonempty subset of the example's 15 sentences across six case bases.
The draft family applies its case rule **before** deleting sentences. Retained
sentences keep their punctuation, use one space within an original paragraph,
and retain the chosen separator between nonempty original paragraphs. It does
not filter on a hash hint. These interpretations address the discrepancy between
the instruction referring to `himself` as an ending and the following sentence.
The serializer passed 65,546 checks, including hard-coded endpoint offsets and
all retention masks. All four sentence runs completed. The sentence case and
quoted-token case searches together screen 10,737,418,240 masks, but only the
prefix survivors are passed to wallet derivation. These are overlapping
search spaces, not that many unique derived wallets.

The new `chapter-edges` family checks every nonempty byte prefix and suffix of
the six fingerprint-verified chapter bases, plus simultaneous cuts of 1–256
bytes from each end. It checks both original and replacement prize addresses
without a hash hint. This extends the old test of 23 common input-length limits.
It preserves every byte inside the selected interval; it does not combine
arbitrary internal edits with clipping. It completed with no match. Its fixture
test independently enumerates permitted substring intervals, including empty
edge-width and CRLF/multibyte boundaries. Its 160 fixture comparisons passed.

## Historical converter behavior

The preserved July 2019 Ian Coleman source keeps the last whole 32-bit units
of raw entropy. For a hex input with 31 digits, it keeps the final 24 digits
and generates nine words. It also permits mnemonic lengths outside modern
BIP39's usual 12–24 words. This actual historical behavior was absent from
the earlier raw-128/fixed-word-count tests.

`historical-input.cjs` executes the preserved upstream entropy parser and
mnemonic generator. The Python model passed 183 comparisons against it,
including short/long inputs, deletion/insertion cases and auto-detected
numeric bases. The batched wallet engine passed 48 independent private-key,
public-key and hash160 comparisons at normal and boundary indices. Each
actual batch also checks independently computed CPU seeds and all requested
addresses for its first, middle and last candidate. A potential winner is
recomputed on CPU and saved only in ignored `FOUND-*` files.

The complete reports are `batch-hash-entry-both-5f7bb5b4757022b1.json`,
`batch-hash-algorithm-both-ab8966c0d52e0e34.json`, and
`source-spans-example-a47ee8fbd3d1de78.json`. The unprefixed hash-entry and
hash-algorithm records are interrupted, slower prototype runs, superseded
by these complete batched runs. Do not add their partial counts again.
The 16,384-entry mixed-line prototype is likewise superseded by the completed
1,572,864-entry result. Source-span and editor reports record the exact earlier
runner fingerprints under which they completed. Later additions to the runner
change its checkpoint filename rather than silently inheriting prior work.

## Run locally

These direct Python commands do not involve PowerShell script policy:

```powershell
Set-Location 'C:\Users\boomb\Downloads\puzzle-investigation'
$py = 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe'
& $py .\assumptions-2026-09-27\batch-assumptions.py --family hash-entry --target both
& $py .\assumptions-2026-09-27\batch-assumptions.py --family hash-algorithm --target both
& $py .\assumptions-2026-09-27\search-assumptions.py --family source-spans --target example
```

To reproduce the unfiltered families and the full quoted-letter family:

```powershell
& $py .\assumptions-2026-09-27\batch-assumptions.py --family source-spans --target example
& $py .\assumptions-2026-09-27\batch-assumptions.py --family editor-forms --target both
& $py .\assumptions-2026-09-27\batch-assumptions.py --family mixed-lines --target example
& $py .\assumptions-2026-09-27\quoted-mask-search.py --join lf
& $py .\assumptions-2026-09-27\quoted-mask-search.py --join crlf
& $py .\assumptions-2026-09-27\structural-search.py --family case --join lf
& $py .\assumptions-2026-09-27\structural-search.py --family case --join crlf
& $py .\assumptions-2026-09-27\structural-search.py --family drafts --join lf
& $py .\assumptions-2026-09-27\structural-search.py --family drafts --join crlf
& $py .\assumptions-2026-09-27\batch-assumptions.py --family chapter-edges --target chapter
```

The byte-position passage search **with** the MD5 prefix completed; its report
is `source-spans-example-698b1fe414b1ad95.json`. It can be reproduced with
`search-assumptions.py --family source-spans --target example --scope bytes`.

**September 28 update:** the corresponding byte-position search **without**
the prefix has completed: 27,130,032 entropy candidates, 189,910,224 address
operations, zero matches. The report is
`batch-source-spans-example-2de1bff733ef265a.json`. The following command is now
for reproduction only; it is no longer a new search recommendation:

```powershell
& $py .\assumptions-2026-09-27\batch-assumptions.py --family source-spans --target example --scope bytes
```

Unlike the smaller token-boundary unfiltered run, this permits cuts inside
words. This family assumes one contiguous deletion
or duplication on one of 12 bases, English/raw MD5, empty passphrase, and indices
0–6. It does not cover every possible historical revision.

Checkpoints bind the candidate sources, code and GPU kernels. They are not
compatible with arbitrary code changes. Existing completed families do not
become new evidence when rerun. Node.js is required for historical fixtures;
the Python/OpenCL dependencies are those already installed for this checkout.

## What remains unresolved

The intended final answer and private key have not been recovered. Reproducing
the solved example's exact answer buffer and claiming method remains a strong
research lead: its raw question matches the published seven-digit MD5 prefix, but its funded
wallet still does not reproduce from the tested interpretations. These negative
results do not identify a unique cause. A missing text revision, simultaneous
edits outside the tested families, or an untested converter configuration can
still explain the mismatch. They do not prove the puzzle impossible.

See [the September 28 audit](../audit-2026-09-28/README.md) for the completed
user runs and the distinction between the verified Stage One control and the
unreproduced example. Solving the latter is not a prerequisite for trusting the
verified Stage One derivation. That audit recommended no further long run;
the subsequent [joint-format follow-up](../joint-format-2026-09-28/README.md)
documents a separate mixed-artifact hypothesis, benchmark and partial pilot.

The next useful external evidence would be the example solver's exact MD5 or
source buffer, or a byte-preserving July 2019 answer copy. No such evidence was
recovered in this pass, and no solver or author was contacted. The user's active
expanded-run checkpoints were left separate and were not relabeled complete.

## Archive retrieval

The Wayback availability API returned a 2023 record for the example, but the
retrieved page contains only a Reddit shell, not the question. A later exact-URL
CDX query confirmed that single capture; the wildcard query returned HTTP 403.
Neither supplies another source buffer.

A renewed CDX query succeeded for Twitter. It returned two records for the
exact `NakamotoAoi` handle. Other returned records use a trailing underscore
and were excluded. The recovered June 25, 2019 tweet only announces a July 7
hint session, linking the already known posting-schedule thread. The second
capture returned no tweet text. This is not a complete Twitter-history audit.
Metadata, retrieved responses and parsed tweet text are saved alongside this
report. No exact final answer buffer or new final-block hint was recovered.

On 2026-09-27, web retrieval of the live Reddit example, discussion, final
block, Block 76, and the two relevant user profiles succeeded. The inspected
comments supplied no complete example/final solution or downloadable July
chapter. The recently reported April archive is for another part. Direct
Arctic Shift follow-up requests failed with HTTP 403/500; these errors are not
evidence of absent comments. No participant was contacted.

At 2026-09-27 02:18 UTC, Mempool returned the original 77,700,000-satoshi output
and Blockstream reported `spent: false`; see `funding-recheck.json`.

Primary references:

- [Example instructions](https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/)
- [Author's unresolved claiming-step comment](https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evwv4rm/)
- [Historical converter truncation](https://github.com/iancoleman/bip39/blob/45e40c288fe0d6cfba2c57a68f421eeb34d41385/src/js/index.js#L1347)
- [Recovered tweet capture](https://web.archive.org/web/20190625232325/https://twitter.com/NakamotoAoi/status/1143660969144401920)
