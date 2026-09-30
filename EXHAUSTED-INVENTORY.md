# Exhausted-search inventory — Quizchain 777 mBTC final block

**Status: UNSOLVED. No winning key or answer recovered. No `FOUND-*` file exists.**

This is the consolidated write-off of everything that has been searched and
excluded, across all sessions. Counts are candidate/address **operations** and
**overlap heavily** — they are not a count of unique wallets. Every "no match"
means only the documented finite family, at the documented settings, was
negative. The baseline mechanism (MD5 of exact UTF-8 → English BIP39 → empty
passphrase → `m/44'/0'/0'/0/i`) is fixed and independently verified by the
positive controls below.

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

Block 29 is the strongest long-text control and calibrates the author's
draft→hash path: **LF, MD5, one paragraph per line, NBSP→double-space, nothing
before/after.** Three independent LF calibrations (Stage One, the example's
published `7759227` prefix, Block 29) outweigh her "13 10" descriptions, which
came from asciivalue.com rather than her hashing tool.

---

## B. This session (2026-09-29 → 09-30): chapter two-toggle matrix

"Change only a couple of letters" = exactly two ASCII case toggles applied on
top of an FFWW baseline. **6 cells × 641,697,400 pairs = 3,850,184,400**, index
0, both targets, GPU-MD5 path, corrected kernel `9429b7fc…`, no prefix filter.
**All complete, no match.**

| FFWW baseline | draft (NBSP→space, LF LF, trailing kept) | rendered (trailing trimmed) | CRLF CRLF joins |
| --- | :--: | :--: | :--: |
| all-four groups | ✅ | ✅ | ✅ |
| first-three groups (excl. quoted Hal ¶230–234) | ✅ | ✅ | ✅ |

Three-toggle on the chapter's 35,825 letters is C(35825,3) ≈ 7.6×10¹² —
infeasible — so this is the practical frontier for the chapter case space.
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

The example claim buffer is **>3 case flips from every obvious reading**; a
pure-case explanation would need 4+ flips (infeasible to brute), pointing to a
formatting/content quirk already covered below.

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
  to the saved API text. `modifyDate` 2019-07-23T23:12Z (the final version).
- Public Aoi archive paginated to exhaustion: 202 posts, 864 comments.
- Wayback CDX for `wattpad.com/720888559*`: **zero captures** (no 2019 page to
  diff); story-page queries returned 503/504 (prove nothing).
- Duplicate `data-p-id` at ¶77 explained (repeated-paragraph disambiguation), not
  an editing clue.
- "Starting Up" says the author lost her solution records; spending the escrow
  later shows key access, not retention of the source text.

---

## F. What is NOT excluded (honest bottom line)

The feasible, well-motivated case-perturbation space around the FFWW method is
now thoroughly covered on both the chapter and the example, along with the
formatting, encoding, path, and passage-edit families. No match. What remains
un-excludable is **not** reachable by more brute force:

1. A case pattern **≥4 letters** from every tested baseline (search space too
   large to enumerate).
2. A **2019 buffer that differs in content** from the archived chapter (no
   archived copy exists to recover it).
3. The **example's exact claim method**, which the author herself did not know
   and which no solver disclosed.

The single highest-value missing input is primary evidence — the example's exact
solved buffer or an archived July-2019 draft — and the available public sources
for it appear exhausted. Absent that, the puzzle is not proven impossible, but
further undirected GPU grinding has low expected value.

*Overlapping operations total across all sessions ≈ 9–10 billion; this is not a
unique-wallet count. See per-directory READMEs and checkpoints for exact,
verifiable bounds.*
