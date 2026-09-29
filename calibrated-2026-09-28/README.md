# Calibrated bases and structured twists, 2026-09-28

**Unsolved. No match in any family below.** This pass started from a new
positive control and primary-source calibration, and did not simply widen an
earlier radius. Every family is bounded, deduplicated by MD5, has no
MD5-prefix filter, and ran through the corrected GPU kernel
(`9429b7fc…0cd2`). At startup, each run detected the solved Stage One and
Grycoin Block 1 controls. Every batch was spot-checked by independent CPU
mnemonic/seed/BIP32/hash160 derivation and by an independent text rebuild.

## New evidence behind the bases

1. **Block 29 reproduced** ([../control-block29-2026-09-28/README.md](../control-block29-2026-09-28/README.md)).
   This is a draft of this very chapter, "exactly same as used for hashing". It
   hashes as raw UTF-8 with **LF**, MD5, one paragraph per line, and nothing
   before or after. The derived WIF ends in `JRu`, block 30's published link.
   That makes three independent LF calibrations. The author's "13 10"
   statements describe asciivalue.com, not her hashing input.
2. **Double spaces, not NBSPs.** All six chapter NBSPs are `NBSP+space`, and
   every trailing run is one ASCII space, with no ASCII multi-space anywhere.
   That is the signature of typed double spaces converted to HTML. The author's
   four Reddit reposts of the Abstract carry two ASCII spaces and match
   paragraph 89 exactly under NBSP→space. The 2019-07-17 part "THOMAS and
   SATOSHI" has `anagram. What` with one space, while the chapter has the double
   space, so the double spaces were typed while assembling the chapter.
3. **Missed line-break doubling is observed behaviour.** The ten `<br>` sites
   are single breaks the author did not double. Paragraph 183 is two separate
   paragraphs of "THOMAS and SATOSHI" merged by one. Her April "Second Life"
   part shows her single-LF draft lines becoming separate paragraphs.
4. **At least one twist remains.** On 2019-07-30 she moved the prize "because I
   wanted to remove *one of the twists I had*". Hashing with two line breaks is
   listed separately ("also"). The pre-migration answer had one line break per
   paragraph (author comment `ev96vwg`).
5. **Tablet workflow.** The part "Mistakes" says she hashes on a tablet with
   a tool whose default is MD5. That agrees with LF input.

The earlier 27 broad shapes include the draft form (`lf-preserve`,
`nbsp-space`, trailing kept), but only with ≤10 toggles inside the 32 FFWW
endpoints or exactly three endpoint toggles. The only completed two-toggle
search used the NBSP-retained base.

## Bases (`twist-search.py`)

Four revised-answer serializations (paragraph joins `\n\n`) × starts 0/1/3:
`draft` (internal `\n`, NBSP→space, tails kept); `rendered` (a browser copy:
NBSP→space, trailing spaces removed at paragraph ends *and before internal
breaks*); `draft-promoted` (internal breaks doubled); `app` (NBSP retained).
Three pre-migration serializations with single `\n` joins × starts 0/1/3:
`draft-single`, `rendered-single`, `app-single`. Both targets are checked on
every candidate.

## Completed families

| Script | Family | Distinct entropies / addresses | Result |
| --- | --- | ---: | --- |
| `twist-search.py` | Per base: 16 FFWW masks × flip styles (both / first-only / last-only) × every subset of the eight adjacent non-FFWW paragraphs 3, 8, 9, 91, 164, 165, 166, 233 × subsets of motifs {block-29 `vOIce` in ¶11, `vOIce` in ¶23, title `SECOND`}; plus 16 masks × **any one or two further paragraph flips**; plus motifs × any one further flip | **12,290,432** (index 0; 12,361,902 enumerated) | none |
| `link-suffix.py` | 21 bases × 16 masks × Stage One key suffix (last 3, last 7, whole WIF) × separator (space, none, blank line), per the `[solution] [link]` format of block 29 | **3,024** | none |
| `linebreak-slips.py`, example | Grycoin Block 2: each of the 9 boundaries independently `\n`, `\n\n`, `\n\n\n` (3⁹) × the six prior case rules; indices 0–6 | **118,098** / **826,686** | none |
| `linebreak-slips.py`, chapter | Bases draft/rendered/app × starts 0/1/3 × all-four and first-three FFWW; one or two slipped sites (a join becomes `\n` or `\n\n\n`; an internal break becomes `\n\n`) | **2,735,880** (index 0) | none |
| `example-context.py` | Grycoin Block 2 answer windows extended into adjacent post paragraphs (`Question:`, `Format:` …), following the verified Stage One `[edited slightly]` precedent × six case rules × rule scope × LF/CRLF × final newline; indices 0–6 | **1,500** / **10,500** | none; no `3c6` survivors |
| `radius-search.py` | `rendered` and `promoted` bases × starts 0/1/3 × ≤6 toggles at the 32 FFWW endpoints (the 27 earlier shapes omitted both bases) | **6,894,102** (6 × 1,149,017; index 0) | none |

Checkpoint `twist-search-9858a1174b7d7ae8.json` binds the configuration,
bases, source hash, code hashes, and GPU and wallet kernel fingerprints. It
recorded 2,291 sampled independent CPU comparisons. Its `code_sha256` for
`twist-search.py` (`49f83899…bb2f`) was taken over the CRLF working copy that
ran. Git stores the same file with LF (`582dfba6…dfd7`); a Windows checkout
with `core.autocrlf=true` reproduces the recorded hash.

### Exact scope of the negatives

They exclude only the listed case patterns on the listed byte bases, at BIP44
index 0 (the example at 0–6), raw MD5, English, empty passphrase. They do not
exclude a different wording of the 2019 draft, other twist types, or more
than two extra paragraphs. They also do not exclude a flipped extra paragraph
combined with endpoint toggles, or other derivation settings. Overlap with
older runs is expected (for example `app` p0 without extras is the canonical
base) and is not double-counted as new coverage.

## Commands

```powershell
Set-Location 'C:\Users\boomb\Downloads\puzzle-investigation'
$py = 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe'
& $py .\calibrated-2026-09-28\twist-search.py --verify-only   # 1,304 serializer/MD5 checks
& $py .\calibrated-2026-09-28\twist-search.py --platform 1     # ~13 min, resumes per base
& $py .\calibrated-2026-09-28\link-suffix.py                   # seconds
& $py .\calibrated-2026-09-28\linebreak-slips.py               # ~5 min alone, ~25 min with a shared GPU
& $py .\calibrated-2026-09-28\example-context.py               # seconds
& $py .\calibrated-2026-09-28\radius-search.py --base rendered --start-paragraph 0 --radius 6
```

`radius-search.py` resumes from `radius-<base>-p<start>-r<radius>.json`; a
different radius is a different checkpoint. Radius 8 is 15,033,173 candidates
per start and radius 10 is 107,594,213.

## Two-toggle searches on the calibrated bases

Earlier only the NBSP-retained LF base had the completed exactly-two-toggle
search. These runs cover the calibrated bases, all-four-group FFWW baseline,
index 0, both prize addresses, GPU-MD5 path, no prefix filter. On an unshared
RTX 4060 they sustain roughly 33k–60k pairs/s (the laptop GPU throttles over a
long run).

Each base is 35,825 letters → 641,697,400 pairs, byte-verified against
`twist-search.py`'s `reference()`. The pair tool toggles any two further
letters on top, i.e. the baseline ± any two single-letter case changes — the
literal "change only a couple of letters".

| Base file | Baseline / serialization | Result |
| --- | --- | --- |
| `four-groups-lflf-nbsp-space.txt` (`0648ab34…`) | all-four FFWW; NBSP→space, LF LF joins, trailing kept (draft) | **complete, no match** |
| `four-groups-lflf-rendered.txt` (`0e6b7242…`) | all-four FFWW; draft minus 13 trailing + 4 pre-`<br>` spaces (browser copy) | **complete, no match** |
| `three-groups-lflf-nbsp-space.txt` (`701f905e…`) | **first-three** FFWW (excludes the quoted Hal paragraphs 230–234); draft | **complete, no match** |
| `three-groups-lflf-rendered.txt` (`1e75b87d…`) | first-three FFWW; rendered | pending |
| `four-groups-crlfjoin-nbsp-space.txt` (`7ed5b097…`) | all-four FFWW; **CRLF CRLF joins**, internal LF, NBSP→space — tests her "13 10 13 10" | **complete, no match** |

`three-groups-*` differ from `four-groups-*` only at the 8 group-4 endpoint
letters, so the all-four ± 2-toggle search (max 2 letters different) could not
reach them. `four-groups-crlfjoin-*` equals the draft base with LF LF joins
replaced by CRLF CRLF (internal single breaks left as LF).

To reproduce (build the draft base, then run; swap in the rendered base for
the second row):

```powershell
& $py -c "from pathlib import Path; b=Path('bases/four-groups-lflf.txt').read_bytes(); Path('bases/four-groups-lflf-nbsp-space.txt').write_bytes(b.decode('utf8').replace(' ',' ').encode())"
& $py .\gpu-case-pairs.py --base .\bases\four-groups-lflf-nbsp-space.txt --all --gpu-md5 --platform 1
```

This is a bounded generalisation of the `vOIce` motif (any two letters
anywhere). It is not an author-confirmed clue. Do not run it concurrently with
another GPU search if a timing comparison matters.

## Corrections to the 2026-09-28 handoff

- `joint-format-2026-09-28/search.py` orders **CRLF first** "because of the
  author's explicit 13,10,13,10 clarification". Three reproduced hashes
  (Stage One, the example's raw `7759227` prefix, block 29) all used LF. The
  "13 10" came from asciivalue.com, so it does not justify CRLF priority. The
  search itself was left untouched because another session is running it.
- Round-1 block 29 was listed only as a precedent. It is reproducible and is
  now the best long-text control (`../control-block29-2026-09-28/`).
- The handoff reported the joint-format pilot at 1,310,720 checked. Its
  checkpoint has since advanced; at this writing a separate process was
  resuming it via `joint-format-2026-09-28/resume.py`. It is still incomplete.

## Ranked remaining explanations

1. **A remaining deliberate twist of a type not yet enumerated.** Evidence:
   "remove one of the twists I had" means at least one twist was kept. The
   families above exclude the obvious paragraph-level, motif and link
   variants. Discriminating test: exactly-two arbitrary toggles on the
   calibrated `draft` base, 641,697,400 candidates, measured ~7.4 h (command
   above). It generalises `vOIce` to any two letters.
2. **The revised text was a copy of the published chapter, not the draft.**
   Evidence: "lost any information on the solution" (2019-07-23), then the
   switch to *display-style* double line breaks. Tested here: the `rendered`
   base with structured twists, slips and ≤6 endpoint toggles. Further test:
   `radius-search.py --base rendered --radius 8` (15,033,173 per start).
3. **Unannounced content drift** between the hashed text and Wattpad. Evidence:
   the chapter was modified 2019-07-23 23:12Z, after publication, and the
   author has a documented history of hashing slips. This cannot be bounded
   without a 2019 copy, and the Wayback prefix `wattpad.com/720888559*` has
   none. The useful new evidence would be the example's exact buffer or a
   solver's disclosure.
4. **A different derivation.** This is the least supported. The historical
   wallet matrix already covers common 2019 wallet settings for canonical
   buffers.
