# Investigation update, 2026-09-26

**Unsolved. No matching key was found.** The live funding output remains
unspent at the check recorded in `chain-status.json` (2026-09-26 08:42 UTC).
This update continues branch `claude/bold-bardeen-b9pir2`, rather than replacing
its earlier searches. Three delegated audits were explicitly run with GPT-6 Sol.

## Reproducibility fixes

Git's `core.autocrlf=true` had normalized all six committed search inputs. A
fresh Windows checkout made the LF and CRLF versions identical, and neither
matched its saved checkpoint hash. `.gitattributes` now marks those files as
byte-preserving inputs. The six files were regenerated from the saved paragraph
JSON; `verify-search-inputs.cjs` checks their known SHA256 values, letter counts,
and checkpoint identities before a search. This does not invalidate the separate
ongoing GPU run: its original on-disk base still matches the recorded digest.

The inherited `brPromote` generator first inserted CRLF pairs and then replaced
every LF with CRLF, introducing extra CR bytes. Its intended CRLF family had
not been tested. The serializer is corrected, and a separate implementation
has now tested every promotion subset with explicit byte assertions.

## Completed searches

All rows below completed in this pass. Counts are operations within each family,
not a count of unique addresses across the combined rows. Every final-chapter
family checks the current and superseded escrow; the example checks its solved
payout address. No row is an exhaustive search of the entire puzzle.

| Family | Text candidates | Derived addresses | Result record |
| --- | ---: | ---: | --- |
| Correct internal-break promotion: 1,024 subsets × raw/three/four groups × two NBSP modes × LF/CRLF; BIP44 indices 0–20 | 12,288 | 258,048 | `verification/corrected-br-results.json` |
| Internal-break deletion: independently retain/delete each of 10 breaks with ordinary spaces preserved; same three bases and two joins/NBSP modes; indices 0–6 | 12,288 | 86,016 | `text/br-deletion-results.json` |
| Historical converter modes on 16 group selections, three starting boundaries and supported whitespace/join/tail choices; indices 0–6 | 576 distinct MD5s; 6,336 entropy derivations | 44,352 | `coleman-mode-results.json` |
| Example block: every subset of 20 paragraph-boundary letter toggles × LF/CRLF, filter published MD5 prefix `3c6`; raw plus ten converter modes; indices 0–20 | 2,097,152 → 518 prefix survivors → 5,698 entropy derivations | 119,658 | `research/coleman-example-results.json` |

**508,074 public addresses were derived in these four runs; no match.** Source
and candidate-stream hashes are recorded where applicable. Known author WIF,
solved Stage One, and Grycoin Block 1 calibration checks passed.

## Historical converter setting

The official [July 2019 Ian Coleman source](https://github.com/iancoleman/bip39/blob/45e40c288fe0d6cfba2c57a68f421eeb34d41385/src/js/index.js#L1321)
uses SHA256 of the **ASCII entropy string** when a fixed mnemonic word count is
selected, then truncates to 128/160/192/224/256 bits. For a typed MD5 hex string,
this differs from raw digest entropy and from SHA256 of the chapter. Uppercase
and lowercase hex also produce different hashes in this setting.

The historical default was **raw**, so this is a manual-setting hypothesis,
not an explanation based on a reset to defaults. Both the chapter and example
tests above found no match within their stated text families. Official source,
license, hashes and 20 independent vectors are retained in `verification/`.

## Evidence audit

The [author's direct example instruction](https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evuthpw/)
is to preserve copied line breaks and change capitalization. Her
[later solver reply](https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evwv4rm/)
admits she does not know the step from the correct letter changes to claiming.
Negative text searches alone therefore do not establish that the answer needed
a larger text edit. A tool or serialization mismatch remains possible.

The renewed thread audit includes other solvers' returned comments in four
relevant threads and puzzleponky's available history. No published complete
example solution was recovered. Twitter archive access remains incomplete;
failed retrievals are recorded, not treated as proof that no hint exists.
See `research/SOLVER_SOURCE_AUDIT.md`.

Fresh Wattpad responses agree with the saved chapter after storage-line-ending
normalization. They confirm 273 paragraphs, 10 internal breaks, 6 NBSPs and 13
paragraphs with trailing spaces. Paragraph IDs do not certify copied internal
newline bytes: they agree with tag-stripped text. See `text/REPORT.md`.

Tablet use does not establish the final hashing workflow. A later spend of the
old escrow proves access to a signing key, not retention of the answer text.
Those earlier inferences have been corrected in the prior report and README.

## GPU progress and remaining work

The pre-existing GPU process continues outside this checkout; it was not
interrupted or duplicated. A snapshot of its LF four-group checkpoint records
next rank **320,065,408 / 641,697,400** at 2026-09-26 08:43:12 UTC. The CRLF
four-group snapshot is **1,104,096 / 641,697,400**. These identify exact intervals
already processed, not completed sweeps. Newer live checkpoints may exist in
the original local checkout.

Finishing all six pair-toggle bases at index 0 remains a bounded computation,
and a negative result would not exclude a different source buffer or edit
family. The strongest missing evidence is the solved example's exact method
or a byte-preserving 2019 answer buffer. Neither was recovered in this pass.

## Reproduce locally

From the repository root, the CPU checks need Node.js only:

```powershell
node .\verify-search-inputs.cjs
node .\verifier.cjs --selftest
node .\verify-stage-one.cjs
node .\followup-2026-09-26\coleman-mode-search.cjs
node .\followup-2026-09-26\research\coleman-example-search.cjs
node .\followup-2026-09-26\verification\corrected-br-search.cjs
node .\followup-2026-09-26\text\br-deletion-search.cjs
```

GPU installation and certification are in the root README. After the current
GPU run finishes, `run-gpu-sweep.ps1` can run all six bases sequentially and
resume their local checkpoints. Keep future `FOUND-*` witnesses local: they
identify spendable keys and are excluded from Git.
