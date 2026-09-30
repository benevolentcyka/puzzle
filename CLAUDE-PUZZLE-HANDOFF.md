# Quizchain 777 mBTC — independent investigation handoff

Copy this document into Claude, or attach it with the repository. It describes
the public challenge and actual research scope plainly. No prompt can guarantee
how another service classifies a request; this is not a request to bypass its
policies or hide the cryptographic work involved.

---

Please help solve AoiNakamoto's publicly advertised 2019 Quizchain 777 mBTC
final-block puzzle. Treat this as an independent investigation: scrutinize
the existing assumptions and code, recover primary-source evidence, and try
to produce an exact answer buffer whose derived Bitcoin address matches the
published puzzle target. If you cannot establish a solution, identify the
strongest genuinely untested explanation and provide a bounded, reproducible,
benchmarked computation that discriminates between explanations.

The task involves offline hashing and deterministic wallet derivation from
the author's public puzzle text. The repository contains the public invitation,
funding transactions, and solved earlier challenges that demonstrate the
mechanism. Limit the investigation to these identified public challenges.
Do not scan unrelated wallets, obtain anyone's nonpublic credentials, access
private systems, contact people, or sign/broadcast transactions. The original
announcement included expiry conditions, including Tanabata 2022. An unspent
output does not establish that an offer is currently open. This request is
for solving and independently verifying the mathematical/text puzzle; it is
not an instruction to spend funds.

## Repository and operating constraints

- Repository: https://github.com/benevolentcyka/puzzle
- Branch: `claude/bold-bardeen-b9pir2`
- Local working folder: `C:\Users\boomb\Downloads\puzzle-investigation`
- Optional earlier reference: `C:\Users\boomb\Downloads\quizchain-investigation`
- Do **not** work in `aria-stack-on-server`, even if the session starts there.
- Windows PowerShell; Python: `C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe`.
- RTX 4060 laptop; the tested OpenCL platform is `1`. Verify platform identity
  on a different machine. Python dependencies and reviewed local GPU source are
  already installed on this machine; consult `requirements-gpu.txt` and
  `setup-gpu.ps1` on a fresh clone.
- PowerShell `.ps1` execution is restricted. Direct `python.exe` commands work
  without changing execution policy. Do not mistake a policy failure for a
  completed search.
- User authorized retaining research/code in this repo and committing/pushing
  to the existing branch. Preserve unrelated changes. Publication is secondary
  to solving. Never commit a new winning key or mnemonic; ignored `FOUND-*`
  files are reserved for local verified matches.
- Do not claim to have read files or checked sources you cannot actually access.
  If you cannot access the repo, ask for the specifically necessary attachments.

## Current status — read before suggesting another run

**UNSOLVED. No final answer or winning key has been recovered.**

The user's latest completed run is real, not hypothetical:

```json
{"next_rank":27130032,"derived_addresses":189910224,"matches":0,"complete":true,"updated_utc":"2026-09-28T07:47:28.760999+00:00","entropy_candidates_total":27130032}
```

It is the unfiltered **example** byte-passage search, not an exhaustive search
of the final chapter. It tested one contiguous deletion or duplication at
every byte boundary over 12 example bases, using English/raw MD5, empty
passphrase, and BIP44 indices 0–6. Exact record:
`assumptions-2026-09-27/batch-source-spans-example-2de1bff733ef265a.json`.
The completion count and runner fingerprints were audited.

The broad final-chapter run is also now actually complete: all 54 checkpoints
for 27 byte shapes, marked-endpoint radius 0–10, and exact triples at any
paragraph endpoint. Older notes that call this only an assumed negative have
been superseded by `audit-2026-09-28/verified-expanded-completions.json`.

Read `investigation-2026-09-30/README.md` and
`EXHAUSTED-INVENTORY.md` first. The 28,194,048-candidate mixed-format
run is now complete with zero matches; old 8,962,048 notes are historical.
The 2026-09-30 pass adds actual wording differences, complete one-ASCII-edit
coverage on six bases, independent nearby initials and all marked paragraph
pairs, plus unusual-capitalization tests. Exact settings/results are below.
No final-target match has been recovered.

## Public challenge and targets

Original announcement and revision:
https://www.reddit.com/r/Grycoin/comments/cgkpbb/777_mbtc_quizchain_last_block/

The announcement points to the final version of the second Wattpad chapter.
The author later moved the prize, removed one twist, and said the revised
answer uses two line breaks between paragraphs.
The original post also discusses the old address's digits, `Ao`, Fibonacci
numbers, and apophenia. These are preserved in archived post `cgkpbb`; they
are not established constraints on the revised answer. Keep both addresses
and the revision chronology explicit when considering those remarks.

| Purpose | Address / funding |
| --- | --- |
| **Revised final target** | `14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W` |
| Revised target hash160 | `2bc16867479a8d01179a6452651abe14a65eb61a` |
| Revised funding | `a1916e7ed9eac3fcc56a55056328cb09d06925e2694f2e6720de12b228514d1f`, output 1, **77,700,000 sats** |
| Superseded final target | `1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC` |
| Original funding | `499bcd420c7f662d2513b440aedd29c4fa829d6c9edb90dfc545e9305466d49f` |
| Separate later format-example target | `1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi` |
| Example hash160 | `09d565074752019721ce68c58548ebc13750d5cc` |
| Example funding | `f11eca9925c7809210796a3c8d95677dfaf0becb4f6df4c74e7261c3011a2e3c`, output 0, **700,000 sats** |

The September 28 chain audit reported the final 77,700,000-sat output unspent.
The example had one funding output and one spend. Responses and timestamps are
in `audit-2026-09-28/chain-audit.json`. Recheck before making a current claim;
on-chain status is not proof of a particular solution or present prize terms.

## Confirmed derivation and positive controls

The baseline verified mechanism is:

1. Preserve a candidate answer's exact UTF-8 bytes.
2. Compute MD5, yielding 16 entropy bytes. Do not accidentally hash the hex
   representation again unless explicitly testing that separate hypothesis.
3. Convert raw entropy to an English BIP39 12-word mnemonic with checksum.
4. Use the empty BIP39 passphrase; PBKDF2-HMAC-SHA512, 2,048 iterations.
5. Derive compressed legacy P2PKH using BIP44 `m/44'/0'/0'/0/i`.
6. Compare the full derived address/hash160 to the specified challenge target.

This mechanism is supported by actual positive controls, not just convention:

| Control | Exact verification |
| --- | --- |
| Solved first stage | 16 saved Hal Finney paragraphs, including `[edited slightly]`; four designated paragraphs get first ASCII letter lowercase and last ASCII letter uppercase; LF LF joins; no final newline. MD5 `9dd2efb9bc976c2095bd534d7b8d431c` → index 0 address `19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN`. |
| Grycoin Block 1 | MD5 of exact bytes `Still 21st Century` → index 0 address `18EpYz5qB3XoxZWouJF3KdEp3E2nfv9FgP`. |
| Author's public derivation vector | Entropy `2941774a2abec9f30c7d6777d1d53d91`, BIP44 index 1 → publicly disclosed WIF `L5Z66qPmUkTAsWQywjRNHDxHrX6J1X1SQedp6V8QsbaXR7rGd6ex`. This is a published test vector, not a newly recovered final-puzzle key. |

Run `node verify-stage-one.cjs` and `node verifier.cjs --selftest` to verify.
`verifier.cjs --file PATH` hashes and derives from an exact candidate file.
Stage One source: https://bitcointalk.org/index.php?topic=155054.0

**Do not mislabel Grycoin Block 2 as a reproduced positive control.** That later
format example was claimed, but this repo has not reconstructed its exact
answer-to-funded-address mapping. It is a useful separate research target,
not a prerequisite for trusting the actual solved controls above.

## Source and primary clues

- Chapter: https://www.wattpad.com/720888559-second
- Text API: https://www.wattpad.com/apiv2/?m=storytext&id=720888559
- Saved response: `wattpad-api-720888559.txt`
- Exact parsed text: `wattpad-paragraphs.json`, **273 strings**. Reconstruct
  according to a stated join/normalization policy; don't copy rendered Markdown
  and assume the resulting bytes are identical.
- Metadata reported `2019-07-23T23:12:04Z` modification, before July 30
  replacement funding. This is evidence about metadata, not a cryptographic
  guarantee of historical content.
- Discussion: https://www.reddit.com/r/Grycoin/comments/chn8un/real_big_block_discussion/
  The author clarified two CRLFs, bytes `13,10,13,10`. Earlier one-break advice
  predates the prize migration. Keep the chronology straight.
- Later explanation: https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/
  The author says both final-block stages keep the long text, changing selected
  letter capitalization. This supports case transformations; it does not
  establish every formatting byte of the copied buffer.
- Previous long-text precedent: https://www.reddit.com/r/bitcoinpuzzles/comments/bc6rkn/easy_7_mbtc_quizchain_block_29/
  That block changed `o` and `i` inside `voice` to `O` and `I`. It also had a
  separate link-suffix condition; don't silently transplant it into the final.
- Author's Stage One linkage:
  https://www.reddit.com/r/Grycoin/comments/chn8un/comment/eve843h/
- Example's raw-hash clue:
  https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evv9k37/
- Author's reply after example claim:
  https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evwv4rm/
  She reported knowing the intended case changes but not how the solver
  proceeded to claim. This leaves a gap; it does not prove a specific bug.
- Solver's Stage One comment:
  https://www.reddit.com/r/Grycoin/comments/ca6jxv/comment/evvmey8/
  The solver says the example helped with Stage One. It supplies no exact final
  hash or input buffer.

### Exact chapter structure used in searches

Zero-based paragraph indices throughout:

```text
FFWW groups:
[4,5,6,7]
[92,93,94,95]
[167,168,169,170]
[230,231,232,234]

Paragraphs with internal LF:
[62,72,120,123,145,159,183,188,192,212]

Paragraphs ending with ASCII spaces:
[85,107,121,127,138,146,164,165,191,200,208,219,266]

Six NBSP occurrences in paragraphs:
89,124,125,125,195,256

Leading title paragraphs:
0: Second
1: I. Second Life
2: 1. Second Coming
```

The all-four-group candidate lowercases the first ASCII letter and uppercases
the last ASCII letter in each of the 16 marked paragraphs. Prior searches
also covered raw text, first-three-group and all 16 coherent group selections,
plus independent case choices at the marked endpoints under specified bounds.

The full saved chapter is 45,456 UTF-8 bytes with LF LF paragraph joins, and
46,000 bytes with CRLF CRLF joins while retaining internal LF. The six NBSPs
are the only non-ASCII characters in the parsed source.

Wattpad `data-p-id` checks matched 272 of 273 paragraphs directly or under
documented whitespace forms. The remaining paragraph, index 77, is the second
`"What?"`. A control chapter showed that repeated paragraphs get disambiguated
IDs: 147 repeated occurrences had distinct IDs while first occurrences matched.
Therefore that one ID mismatch is **not** evidence of a changed July draft.
See `verify-wattpad-ids.py`, `wattpad-paragraph-audit.json`, and
`wattpad-id-control.json`.

### Later example: important unresolved facts

The example's question has 10 paragraphs, 15 sentences, 1,549 ASCII bytes with
LF LF joins, and 1,197 letters. Its unmodified MD5 is our computation:
`7759227d7406d8230d7e3a8f7b9846d7`.
**Only the seven-digit prefix `7759227` was published by the author.**
CRLF CRLF gives `e997007971f6f17c8775d83f30edb4c6` instead.

The published intended-answer hint is prefix `3c6`. Obvious FFWW case changes
give LF MD5 `31bf6e2350ad1a91e2a78b1bc48266ea`, not a reproduced prize address.
The prose calls the final `f` in `himself` an ending even though another
sentence follows it in the published paragraph. Removed/split-sentence drafts
and many broader alternatives have already been tested.

An MD5-prefix-filtered negative excludes only candidates passing that filter.
It cannot exclude a typo in the hint or a candidate outside it. Numerous
unfiltered follow-ups are explicitly recorded below. Do not apply `3c6` to
the final chapter; no such final-chapter hash prefix is established.

## Research coverage and limits

The public Aoi archive was paginated to exhaustion of what that provider
returned: **202 posts and 864 comments**, April 2–August 4, 2019, saved in
`aoi-posts-archive.json` and `aoi-comments-archive.json`.
See `AUTHOR_AUDIT.md` for source IDs and retrieval details. This is not a claim
that every deleted, unarchived, or later-edited item was recovered.

The separate Wattpad `Starting Up` part says the author lost solution records
after shutting down/restarting. That statement does not establish mathematical
impossibility. Available solver comments were audited; no exact final buffer
or full solution was found. A recent offered April archive concerns part
717956015, not the July chapter 720888559. Do not confuse the two.

Wayback's recovered example capture was a 2023 Reddit shell, not another
question buffer. The recovered June 25 Twitter post announced a known July 7
hint schedule. Failed HTTP requests are not evidence of absent material.
No author or solver has been contacted in this work.

## Exhausted searches — preserve the bounds

All counts below are candidate/address **operations**, often overlapping, not
a grand total of unique wallets. “No match” means only the documented finite
family and settings were negative. Verify the relevant saved checkpoint before
using a finer-grained exclusion.

### Final chapter and historical wallet settings

| Completed family | Scope and negative result |
| --- | --- |
| Exactly two arbitrary ASCII case toggles | **641,697,400** pairs, corrected GPU arithmetic, all-four-group LF baseline, BIP44 index 0. Only this full pair baseline completed; don't mark other pair baselines complete. |
| Marked endpoint radius ≤10 | All 27 byte shapes × 107,594,213 candidate masks = **2,905,043,751** address operations, index 0. |
| Exactly three arbitrary paragraph-endpoint toggles | Same 27 shapes, **709,943,940** operations, index 0. |
| Historical wallet matrix | 672 example and 576 chapter canonical buffers × eight wordlists × 11 raw/fixed entropy settings × documented historical paths: **27,785,472** operations. Includes 13 path presets, hardened Core address indices, accounts/change variants, roots, and indices 0–20. |
| Independent trailing-space subsets | All 2^13 trim choices, 16 coherent group selections, global NBSP retain/space, global internal LF/CRLF, two paragraph joins; full chapter from index 0; address indices 0–6: **7,340,032** operations. |
| Independent NBSP choices | All 3^6 retain/space/delete choices × 384 group/title/global-trim/join/tail shapes; indices 0–20: **5,878,656** operations. |
| Internal-break deletion / promotion | Each of ten breaks independently deleted in one run or promoted to a paragraph separator in another, with documented raw/three/four-group, global-NBSP and line-ending policies. These are separate families, not all combinations with independent trailing-space and NBSP edits. See the text/verification scripts and result files. |
| Chapter clipping, no hint | Every prefix/suffix of six byte-exact bases, plus simultaneous 1–256-byte removal at each end; 941,946 distinct-per-base entropies, indices 0–6: **6,593,622** operations. |
| Nested WIF / previous-stage continuation | Bounded checks of known prior mechanics; no match. Scope is in `nested-wif-search.cjs`, `nested-results.json`, and earlier research notes, not every conceivable recursive derivation. |

The 27 broad byte shapes are starts 0/1/3 × space policies retain / NBSP-to-space
/ NBSP-to-space-plus-trim × LF throughout / CRLF joins with LF internal breaks
/ CRLF throughout. They use whole-text global policies, not independent mixtures
at every formatting artifact.

### Example and cross-target assumptions

`followup-2026-09-26/POST_PAIR.md` and `post-pair-ledger.json` preserve **36
completed reports totaling 278,101,729 overlapping address operations**. They
include the trailing-space/NBSP rows above and:

- All case subsets of 21 paragraph/explicit-word endpoints, including the
  named `himself` position; published, removed-sentence, split-sentence drafts;
  LF/CRLF and extra joins, with unfiltered coverage as documented.
- One character insertion/replacement/deletion or adjacent transposition using
  106 characters, including whitespace/Unicode artifacts, on canonical drafts.
- Eight 2019 wordlists: English, Japanese, Spanish, Chinese simplified and
  traditional, French, Italian, Korean; raw plus ten fixed-word-count settings.
- Exact `3c6` and, in separate families, one wrong hint digit; these remain
  restrictions, not universal exclusions.
- UTF-8 BOM, UTF-16 LE/BE with/without BOM, terminal LF/CRLF variants, and
  language/index coverage. The largest completed encoding/hint-typo family
  accounted for **97,758,969** address operations.
- 672 obvious example answer variants without any hint filter under all eight
  languages and the documented entropy settings.

`assumptions-2026-09-27/README.md` records further completed families:

| Family | Address operations / limit |
| --- | ---: |
| Historical hex-entry errors across 1,248 canonical buffers | **8,773,310**; one missing/inserted/substituted/transposed hex digit, clipped/reversed/double-pasted input; no hint filter |
| Alternative hash algorithms across those buffers | **314,496**; documented full/truncated/double-hash forms; no hint filter |
| Example token-boundary passage deletion/duplication, no hint | **25,739,084** |
| Example byte-boundary passage deletion/duplication, no hint — user's latest run | **189,910,224**, from **27,130,032** entropy candidates |
| Corresponding byte-passage family with `3c6` | **47,390**; 6,770 survivors from 29,148,216 attempted edits |
| Coherent editor transformations, no hint | **1,060,416**; smart punctuation, UTF/escaped/HTML forms, named replacements and global case policies |
| All independent LF/CRLF choices at 18 example newline bytes | **11,010,048**; six capitalization bases; no hint filter |
| All 2^32 paragraph/quoted-token endpoint case masks, both joins | **14,679,063** derived addresses; only `3c6` survivors |
| All 2^30 sentence-endpoint case masks, both joins | **3,671,479** derived addresses; only `3c6` survivors |
| Every nonempty subset of the 15 sentences | **2,752,428**; six case bases, both joins, case applied before deletion, no hint filter |

The 32-endpoint and 30-endpoint families screened **10,737,418,240 masks**
together, but only prefix survivors were derived into wallets. Never report
that figure as 10.7 billion checked wallet addresses.

Further `audit-2026-09-28/public-wallet-result.json` bounded stale-input test:
1,121 public records created before the example funding block; 4,287 extracted
text values; MD5/SHA256 plus literal public hexadecimal inputs → 8,735 distinct
entropies × indices 0–20 = **183,435** addresses; plus **32** compression-form
checks from 16 checksum-valid **published** WIFs. No target matched; both
positive controls were detected. This does not reconstruct all historical
solution/link/TOMI combinations. Record creation time does not exclude later
edits to archived text.

### Invalid or superseded results

An early third-party GPU secp256k1 `reduce512` bug discarded carries. Its
pre-repair negatives are invalid and saved under `gpu-suspect-snapshots`.
Do not count the old 330,813,312-rank partial pair result as excluded work.
The corrected full pair completion supersedes it.

Corrected crypto-kernel fingerprint:
`9429b7fc2cd5499ceb2993d2d375b8213ca7be61a6a2c4dae0ed1dc7cf0e0cd2`.
The repair passed 65,541 Python modular-reduction comparisons, 8,192 full
independent wallet comparisons, and a further 4,096-address root probe.
See `followup-2026-09-26/POST_PAIR.md` and its arithmetic reports.

Some prototype checkpoints are partial and superseded by complete batched
versions. Do not add their counts again. A changed source, generator, wordlist,
path, kernel, or candidate ordering needs an identity check; do not silently
reuse old progress under a different search definition.

## Actual additional tests, 2026-09-30

| Family | Checked / total candidate operations | Address operations | Result |
| --- | ---: | ---: | --- |
| Documented earlier wording and quote variants | 3,149,568 / 3,149,568 | 22,046,976 | COMPLETE, no match |
| One ASCII deletion or adjacent duplication, six chapter bases, indices 0–6 | 547,508 / 547,508 | 3,832,556 | COMPLETE, no match |
| One ASCII edit, all four operations, six chapter bases, index 0 | 53,715,176 / 53,715,176 | 53,715,176 | COMPLETE, no match |
| Independent nearby initials, indices 0–6 | 196,608 / 196,608 | 1,376,256 | COMPLETE, no match |
| Every subset of 16 marked paragraph pairs, indices 0–6 | 3,145,728 / 3,145,728 | 22,020,096 | COMPLETE, no match |
| Unusual capitals with voice/title motifs, indices 0–6 | 524,288 / 524,288 | 3,670,016 | COMPLETE, no match |
| Unusual capitals combined with nearby initials, index 0 | 25,165,824 / 25,165,824 | 25,165,824 | COMPLETE, no match |
| Independent nearby first AND last endpoints, index 0 | 278,528 / 50,331,648 | 278,528 | PARTIAL, no match |

These counts are overlapping operations, not unique addresses. Read the actual
checkpoint and the family README; do not promote the 262,144 nearby-endpoint
pilot to a completed 50-million-candidate negative.

Primary-source differences:
`source-variants-2026-09-30/README.md` documents six earlier wordings,
three whitespace differences and the Finney spelling `facinating` versus
chapter `fascinating`. The family also tries quote delimiters and whole
earlier sections. It does not guess arbitrary historical prose.

Human-scale case gaps:
The old structured-twist runner couples both ends of extra paragraphs. The
new tests distinguish independently selecting their initial `I` letters
(`I STNM`) and independently including each of the 16 marked paragraph
pairs. Radius 10 around 32 endpoints is not the full paired-paragraph space.
Seven unusual interior uppercase letters and the documented voice/title
motifs supply another finite family. Their combinations are explicitly labeled.

Audit corrections:
Block 29 is now a reproduced long-text positive control, MD5
`982301b80b30af3a0abe110269b0dd43` with link `zff`, LF draft,
funded address `1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P`; WIF suffix
`JRu` agrees with the next block's published link.
It contains no NBSP and cannot prove NBSP handling in the final chapter.
Only the FFWW example baseline has completed unfiltered ≤3 case coverage;
other baselines have ≤2. A separate 11,130-tail replay resolves its stale
derived counter without rewriting the original checkpoint.

## Prepared next command

The broader nearby-endpoint family independently toggles both ends of eight
nearby paragraphs on 768 coherent FFWW/serializer/start/tail bases. It has
**50,053,120 untested candidates** after the partial pilot, index 0, raw MD5,
English BIP39, empty passphrase, both final targets, no prefix filter.

```powershell
Set-Location 'C:\Users\boomb\Downloads\puzzle-investigation'
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\near-case-2026-09-30\search.py --endpoints both --indices 0 --platform 1
```

The initial 262,144 took 10.7 seconds with shared GPU load. Plan 20–40 minutes,
then use the live estimate. Same arguments resume automatically. Hash-prefix
matches are insufficient; every address hit requires CPU reconstruction.
Further source analysis may have higher value than simply increasing a count.

## What I want from you

1. Read the real source, relevant author comments, verification code, and
   completion ledgers. Separate author statements, solver testimony, measured
   facts, and hypotheses. Check for any mistaken exclusion in this handoff.
2. Analyze the chapter's actual clue structure and earlier solved formats.
   Do not fixate solely on GPU throughput or mistake many negative operations
   for proof of one remaining answer.
3. Investigate the unresolved example if it offers a concrete route to new
   information, while remembering that Stage One is already independently
   reproduced. Distinguish unavailable historical bytes from verified current
   source. Do not treat the duplicate Wattpad paragraph ID as an editing clue.
4. Give a short ranked set of genuinely different remaining explanations,
   each tied to evidence and a discriminating test. Explicitly compare a
   proposed search against the exhausted bounds above before running it.
5. Implement and validate the most useful bounded test you can justify.
   Supply exact commands, count, estimated cost from a benchmark, resume
   behavior, positive controls, and precise scope of a negative result.
6. For a proposed solution, provide exact reproducible bytes, MD5, derivation
   settings and independently reproduced target address. Save any new secret
   only in ignored local `FOUND-*` files. A matching hash prefix alone is not
   a solution. Do not invent a successful run or publish a guessed key.
7. If no match is found, say so and record what the run actually excluded.
   Don't simply reissue the exhausted byte-passage/radius-10 commands or label
   an unrun family complete. Leave a useful, verifiable research trail.

Start by stating what the existing evidence really establishes, what you
found missing or incorrect, and which next investigation has the best rationale.
Then do the work you can perform in the available environment.

## Repository reading map

| Purpose | Files |
| --- | --- |
| Latest additional runs and limits | `investigation-2026-09-30/README.md`, `EXHAUSTED-INVENTORY.md`, `source-variants-2026-09-30/`, `single-edit-2026-09-30/`, `near-case-2026-09-30/`, `case-motifs-2026-09-30/` |
| Latest completed user runs | `audit-2026-09-28/README.md`, `verify-completions.py`, `verified-expanded-completions.json` |
| Completed mixed-format run and recovery history | `joint-format-2026-09-28/README.md`, `search.py`, `joint-format-*.json` |
| Exact chapter | `wattpad-paragraphs.json`, `wattpad-api-720888559.txt`, `bases/` |
| Public author history | `AUTHOR_AUDIT.md`, `aoi-posts-archive.json`, `aoi-comments-archive.json` |
| Independent controls | `verifier.cjs`, `verify-stage-one.cjs`, `verify-search-inputs.cjs` |
| Chapter provenance/duplicate IDs | `verify-wattpad-ids.py`, `wattpad-paragraph-audit.json`, `wattpad-id-control.json` |
| Corrected GPU arithmetic and follow-ups | `followup-2026-09-26/POST_PAIR.md`, `post-pair-ledger.json`, `gpu-arithmetic-results.json`, `research/SOLVER_SOURCE_AUDIT.md` |
| Broad chapter / historical paths | `expanded-2026-09-26/README.md`, `chapter-subsets.py`, `historical-wallets.py`, associated checkpoints |
| Hash/input/source/case hypotheses | `assumptions-2026-09-27/README.md`, scripts and completed `batch-*`, `quoted-*`, `structural-*` records |
| Chain and public stale-input audit | `audit-2026-09-28/chain-audit.json`, `public-wallet-result.json`, `public-wallet-audit.py` |

Paths after a directory-qualified entry in a row are relative to that same
directory unless they clearly name a root-level file. If a summary conflicts
with an exact checkpoint and source, investigate the discrepancy rather than
quietly selecting the more optimistic account.
