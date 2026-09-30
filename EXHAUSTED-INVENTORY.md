# Exhausted-search inventory — Quizchain 777 mBTC final block

**Status: UNSOLVED. No final-target key or answer recovered.** The solved historical Block 29 has an ignored local `FOUND-block29.json`; it is a positive control, not the final prize.

This is the consolidated write-off of everything that has been searched and
excluded, across all sessions. Counts are candidate/address **operations** and
**overlap heavily** — they are not a count of unique wallets. Every "no match"
means only the documented finite family, at the documented settings, was
negative. The baseline mechanism (MD5 of exact UTF-8 → English BIP39 → empty
passphrase → `m/44'/0'/0'/0/i`) is independently verified on the
positive controls below; its applicability to the final answer is a strong
working hypothesis, not proof of the final settings.

Targets throughout: revised `14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W` and superseded
`1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC` (final block); `1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi`
(the example / Grycoin Block 2).

---

## A. Verified positive controls (these reproduce — the method is sound)

| Control | Result |
| --- | --- |
| Quizchain Stage One (Hal Finney post, FFWW first-lower/last-upper, LF LF) | MD5 `9dd2efb9…` → `19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN` ✓ |
| Grycoin Block 1 (`Still 21st Century`) | → `18EpYz5qB3XoxZWouJF3KdEp3E2nfv9FgP` ✓ |
| Author's published WIF vector (entropy `2941774a…`, index 1) | → `L5Z66q…d6ex` ✓ |
| **Round-1 Block 29** (draft of *this chapter*; `vOIce`, LF, link `zff`) | MD5 `982301b8…` → `1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P` ✓; derived WIF ends `JRu` = block-30's published link ✓ |

Block 29 is a long-text positive control: LF, MD5, one paragraph per line,
and no material outside its specified answer/link. Its draft contains no
NBSP, so it does not calibrate NBSP handling. The NBSP→space hypothesis comes
separately from the author's public Abstract reposts and HTML double spaces.
The example's `7759227` prefix calibrates its raw LF text, not its unreproduced
claim buffer. The author's CRLF descriptions keep that final hypothesis open.

---

## B. This session (2026-09-29 → 09-30): chapter two-toggle matrix

The two-toggle matrix interprets "a couple of letters" as two ASCII case toggles on
top of an FFWW baseline. **6 cells × 641,697,400 pairs = 3,850,184,400**, index
0, both targets, GPU-MD5 path, corrected kernel `9429b7fc…`, no prefix filter.
**All complete, no match.**

| FFWW baseline | draft (NBSP→space, LF LF, trailing kept) | rendered (trailing trimmed) | CRLF CRLF joins |
| --- | :--: | :--: | :--: |
| all-four groups | ✅ | ✅ | ✅ |
| first-three groups (excl. quoted Hal ¶230–234) | ✅ | ✅ | ✅ |

Three-toggle on the chapter's 35,825 letters is C(35825,3) ≈ 7.6×10¹² —
infeasible as a uniform search. Structured case families can still be small.
(A prior session had done only the all-four **NBSP-retained** LF cell.)

## B2. This session: cracking the solved example (Grycoin Block 2)

The example prize was claimed in 2019, so a buffer exists; the author said it
helps the final and that she does not know how it was claimed. Prior big
example case sweeps derived only `3c6`-prefix survivors; these are **unfiltered**
against the real `1tzie…` address (plus both prizes), index 0.

| Baseline (MD5) | ≤2 toggles (717,004) | ≤3 toggles (285,846,394) |
| --- | :--: | :--: |
| raw `7759227d` | ✅ no match | — |
| ffww-quad `31bf6e23` (= "obvious FFWW") | ✅ no match | ✅ no match |
| non-itasm `36f6f7bf` | ✅ no match | — |
| author `a3bbc2d7` (I→i, himself→himselF) | ✅ no match | — |

At index 0, the example claim is outside ≤3 case changes from **FFWW**;
only ≤2 is excluded from the other three baselines. The original triple
checkpoint omitted the final 11,130 operations from its `derived` counter,
though its final flush was checked. That exact tail was independently replayed
without a match: `source-variants-2026-09-30/example-tail-recheck.json`.

---

## C. Earlier calibrated families (2026-09-28) — all complete, no match

| Family | Operations |
| --- | ---: |
| Structured twists on 21 calibrated bases (flip styles × 8 adjacent ¶ × `vOIce`/`SECOND` motifs × ≤2 extra ¶ flips) | 12,290,432 |
| Stage One key suffix appended (`[solution] [link]`) | 3,024 |
| Per-boundary line-break slips — chapter | 2,735,880 |
| Per-boundary line-break slips — example (idx 0–6) | 826,686 |
| Example windows extended into adjacent post text (idx 0–6) | 10,500 |
| `rendered` + `promoted` bases, ≤6 endpoint toggles | 6,894,102 |

---

## D. Pre-session exhausted families (from the handoff ledgers) — no match

### Final chapter / historical

| Family | Operations |
| --- | ---: |
| Exactly two arbitrary case toggles (all-four **NBSP-retained** LF baseline) | 641,697,400 |
| Marked-endpoint radius ≤10 (27 byte shapes × 107,594,213) | 2,905,043,751 |
| Exactly three arbitrary paragraph-endpoint toggles (27 shapes) | 709,943,940 |
| Historical wallet matrix (wordlists × entropy modes × 13 paths × indices) | 27,785,472 |
| Independent trailing-space subsets (2¹³ × 16 group sels × …) | 7,340,032 |
| Independent NBSP choices (3⁶ × shapes) | 5,878,656 |
| Chapter clipping, no hint (prefix/suffix + 1–256-byte end removal) | 6,593,622 |
| Internal-break deletion / promotion families | (bounded) |
| Nested / previous-stage WIF continuation | (bounded) |
| Mixed-format joint search (2–3 sites, ≥2 artifact classes) | 28,194,048 |

### Example & cross-target (POST_PAIR = 36 reports, 278,101,729 ops) plus

| Family | Operations |
| --- | ---: |
| Example byte-boundary passage delete/duplicate, no hint | 189,910,224 |
| Example token-boundary passage delete/duplicate | 25,739,084 |
| All independent LF/CRLF at 18 example newlines (6 case bases) | 11,010,048 |
| 2³² paragraph/quoted-token endpoint masks (only `3c6` survivors derived) | 14,679,063 |
| 2³⁰ sentence-endpoint masks (only `3c6` survivors) | 3,671,479 |
| Every nonempty subset of the 15 sentences | 2,752,428 |
| Historical hex-entry faults across 1,248 buffers | 8,773,310 |
| Alternative hash algorithms across those buffers | 314,496 |
| Coherent editor/clipboard transforms | 1,060,416 |
| Encoding/hint-typo family (BOM, UTF-16, terminal LF/CRLF, one wrong hint digit) | 97,758,969 |
| 672 obvious example variants × 8 wordlists, no filter | (in POST_PAIR) |
| Public stale-input reuse (records before the example funding block) | 183,435 |

---

## E. Source / provenance work (no new secret found)

- All 33 public Wattpad parts captured by SHA-256; the chapter is byte-identical
  to the saved API text. `modifyDate` 2019-07-23T23:12Z (reported metadata, not proof of the hashed 2019 buffer).
- Public Aoi archive paginated to exhaustion: 202 posts, 864 comments.
- Wayback CDX for `wattpad.com/720888559*`: **zero captures** (no 2019 page to
  diff); story-page queries returned 503/504 (prove nothing).
- Duplicate `data-p-id` at ¶77 explained (repeated-paragraph disambiguation), not
  an editing clue.
- "Starting Up" says the author lost her solution records; spending the escrow
  later shows key access, not retention of the source text.

---

## F. New work, 2026-09-30

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

See `investigation-2026-09-30/results.json` and the four new family
directories. The source prototype and slow edit pilot are superseded and
overlap the completed authoritative runs.

## G. What remains open

More finite, feasible families still exist. Do not equate billions of overlapping
negative operations with proof that only unreachable brute force remains.

- Case choices outside the listed radii/baselines. Three arbitrary chapter
  case changes are ~7.6×10¹², but structured clue-derived subsets can be small.
- Combinations of content edits, case edits, formatting choices and converter
  modes that were tested separately, not as their full Cartesian product.
- Other historical hash-input content, multiple edits, transpositions,
  non-ASCII edits, or alternate derivation settings on new text variants.
- The solved example's exact buffer and the July-2019 buffer remain missing.
  The zero-capture query and returned public archive do not prove no other
  primary record exists.

The latest commands and benchmark are in
`different-approach-2026-09-30/README.md`. No match is a negative for that exact
family only. `CLAUDE-PUZZLE-HANDOFF.md` gives the full public-puzzle context
without promising a solution or another service's policy classification.

## H. Combined section formatting and I signatures

Snapshot 2026-09-30T09:46:13.992341+00:00. The earlier nearby-endpoint run is actually complete,
50,331,648 candidates, zero matches.

| Family | Text operations checked / total | Address operations | Status |
| --- | ---: | ---: | --- |
| Chapter: independent formatting in three sections, voice retained/vOIce | 3,919,104 / 3,919,104 | 27,433,728 | COMPLETE, 0 matches |
| Chapter: I-STNM signatures first,nearest,all, group masks 15,7,0,1,2,3,4,5,6,8,9,10,11,12,13,14 | 11,757,312 / 11,757,312 | 82,301,184 | COMPLETE, 0 matches |
| Chapter: I-STNM signatures 60 remaining selections, group masks 15,7 | 65,536 / 29,393,280 | 458,752 | PARTIAL, 0 matches |
| Example: boundaries, 1 defect(s), independent case choices, prefix 3c6 | 264,241,152 / 264,241,152 | 450,051 | COMPLETE, 0 matches |

The example row filters `3c6`; chapter rows have no prefix filter. Counts
overlap all previous work. Source comparison across all 33 Wattpad parts plus
202 posts and 864 comments found no additional close draft wording at its
specified 0.88 threshold. See `different-approach-2026-09-30/source-audit.json`.
The other 60 I subsets on independently formatted sections form the next
finite family: 29,393,280 candidates at group masks 15/7, indices 0–6.
The exact command has checked **65,536 / 29,393,280** candidates, with zero matches.
It successfully resumed from rank 32,768 to 65,536; **29,327,744 remain**.
