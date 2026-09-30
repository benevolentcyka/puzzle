"""Refresh the factual investigation reports from actual local checkpoints."""
from pathlib import Path
import datetime,json,hashlib,re
ROOT=Path(__file__).resolve().parent.parent
T=chr(96)
def read(p):return (ROOT/p).read_text(encoding='utf8').replace('\r\n','\n')
def write(p,s):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((s.rstrip()+'\n').encode())
def state(p):return json.loads((ROOT/p).read_bytes())
RUNS=[
 ('Documented earlier wording and quote variants','source-variants-2026-09-30/source-variants-7c2afdfd24a61177.json','instances_total'),
 ('One ASCII deletion or adjacent duplication, six chapter bases, indices 0–6','single-edit-2026-09-30/one-edit-small-calibrated-363a578fcac18905.json','candidates_total'),
 ('One ASCII edit, all four operations, six chapter bases, index 0','single-edit-2026-09-30/one-edit-all-calibrated-fb17a2b64e5cca12.json','candidates_total'),
 ('Independent nearby initials, indices 0–6','near-case-2026-09-30/near-first-08c84821d7c87881.json','candidates_total'),
 ('Every subset of 16 marked paragraph pairs, indices 0–6','near-case-2026-09-30/paired-035183d9fccd4383.json','candidates_total'),
 ('Unusual capitals with voice/title motifs, indices 0–6','case-motifs-2026-09-30/motifs-2df38f2995aafb33.json','candidates_total'),
 ('Unusual capitals combined with nearby initials, index 0','case-motifs-2026-09-30/motifs-58a18cc2f3573436.json','candidates_total'),
 ('Independent nearby first AND last endpoints, index 0','near-case-2026-09-30/near-both-6555be4d17950571.json','candidates_total'),
]
rows=[];records=[]
for name,p,key in RUNS:
 s=state(p);assert 0<=s['next_rank']<=s[key] and s['complete']==(s['next_rank']==s[key])
 assert s['derived_addresses']==s['next_rank']*len(s['configuration']['indices'])
 result='COMPLETE, no match' if s['complete'] and not s['matches'] else 'PARTIAL, no match' if not s['matches'] else 'MATCH — inspect local evidence'
 rows.append(f"| {name} | {s['next_rank']:,} / {s[key]:,} | {s['derived_addresses']:,} | {result} |")
 records.append(dict(name=name,path=p,checkpoint_sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),checked=s['next_rank'],total=s[key],addresses=s['derived_addresses'],complete=s['complete'],matches=s['matches'],elapsed_search_seconds=s.get('elapsed_search_seconds')))
table="| Family | Checked / total candidate operations | Address operations | Result |\n| --- | ---: | ---: | --- |\n"+'\n'.join(rows)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
write('investigation-2026-09-30/results.json',json.dumps(dict(updated_utc=now,runs=records,note='Overlapping operations, not globally unique addresses. Current final puzzle remains unsolved.'),indent=2))
NEXT=rf"""Set-Location 'C:\Users\boomb\Downloads\puzzle-investigation'
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\near-case-2026-09-30\search.py --endpoints both --indices 0 --platform 1"""
source_report=f"""# Documented source alternatives, 2026-09-30

**UNSOLVED.** The complete source-variant run checked **3,149,568** entropies
and **22,046,976** addresses, indices 0–6, no prefix filter, zero matches.
{T}source-variants-7c2afdfd24a61177.json{T} is authoritative; its measured
search time is 317.782 seconds and it records 8,085 sampled CPU wallet
comparisons. Candidate overlap with other runs is expected.

## Why these are different candidates

The [original Finney post](https://bitcointalk.org/index.php?topic=155054.0)
spells a word at the end of its paragraph 4 as {T}facinating{T}; final chapter
paragraph 233 spells it {T}fascinating{T}. That is a content difference,
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

{T*3}powershell
& 'C:\\Users\\boomb\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' .\\source-variants-2026-09-30\\search.py
{T*3}

The existing complete checkpoint returns without repeating the family.
A fresh clone needs the two ignored source HTML files: use
{T}fetch-sources.py{T}, which verifies them against the committed manifest.
The prototype {T}source-variants-e92eaa4a6a257540.json{T} checked 65,536
instances before a tuple/list resume mismatch was corrected. It remains local,
superseded by the complete run; its operations are not additional coverage.

## Example counter audit

The completed FFWW example ≤3 checkpoint reports rank 285,846,394 but
{T}derived=285,835,264{T}. Inspection showed that the final {T}flush(){T}
derives/checks the tail, then fails to update that counter. We did not rewrite
the historical record. {T}recheck-example-tail.py{T} independently unranked
and replayed ranks **[285835264, 285846394)**: **11,130** candidates, index 0,
all three public targets, no match. Its proof/result is
{T}example-tail-recheck.json{T}. Only the FFWW baseline has a completed
unfiltered ≤3 example search; raw, non-ITASM and author baselines have ≤2.
"""
write('source-variants-2026-09-30/README.md',source_report)
single=state(RUNS[2][1]);small=state(RUNS[1][1]);old=state('single-edit-2026-09-30/one-edit-all-calibrated-15900d4b164174e4.json')
write('single-edit-2026-09-30/README.md',f"""# Single ASCII copying/editing faults, 2026-09-30

**UNSOLVED.** The complete fast run checked **53,715,176** candidate/address
operations at index 0, both final targets, zero matches. The deletion/duplication
run separately checked 547,508 candidates at indices 0–6 (3,832,556 addresses),
zero matches. The index-0 portions overlap; do not add them as unique wallets.

## Exact finite scope

Six existing chapter bases: all-four or first-three FFWW groups × draft
LF LF/NBSP→space, rendered LF LF/trailing-trimmed, or CRLF CRLF joins with
internal LF preserved. All six include the title and leading headings.

Each candidate performs exactly one operation:

- Delete one ASCII byte, including a space, tab or line break.
- Duplicate one existing ASCII byte immediately before itself.
- Replace one ASCII byte with tab/LF/CR or printable ASCII (98 values).
- Insert one of those 98 values at a UTF-8 character boundary, including
  before/after the complete input.

Identity replacements and single case-bit-only replacements are excluded:
the earlier completed case sweeps already cover these. This does not enumerate
adjacent transpositions, multiple content edits, non-ASCII insertions, other
starting paragraphs, or arbitrary case edits combined with content changes.

The copied-source spelling difference described in
[../source-variants-2026-09-30/README.md](../source-variants-2026-09-30/README.md)
motivates testing a small content mismatch. It does not establish that the
author made one.

## Verified engine and result

{T}search.py{T}/{T}single-edit.cl{T} are the initial byte-by-byte implementation.
It passed 5,733 independent MD5/enumeration fixtures. Its all-operation pilot
reached **{old['next_rank']:,}** before replacement by the faster implementation;
the old checkpoint remains partial and is superseded, not added as coverage.

{T}search-fast.py{T}/{T}fast-edit.cl{T} use word-based reconstruction and
vectorized enumeration. They passed **7,781** independent checks, including
changed MD5 padding boundaries, arbitrary binary short fixtures, independent
edit ordering, and 2,048 full-chapter edit checks. Every search batch samples
first/middle/last MD5s against {T}hashlib{T}, and independently checks BIP39,
PBKDF2, BIP32, public keys and full hash160 on CPU. Stage One and Grycoin
Block 1 are actual matching positive controls. Matches stay in ignored
local {T}FOUND-*{T} files after CPU confirmation.

The faster run restarted at rank 0 under a new code/kernel fingerprint;
no checkpoint was renamed or transferred. The authoritative checkpoint is
{T}one-edit-all-calibrated-fb17a2b64e5cca12.json{T}. Its recorded search time is
**{single['elapsed_search_seconds']:.1f}s**, on this RTX 4060, including periods
with another GPU job sharing the device.

## Reproduce

{T*3}powershell
& 'C:\\Users\\boomb\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' .\\single-edit-2026-09-30\\search-fast.py --family all --indices 0
{T*3}

This complete checkpoint skips the search. A different index list defines a
different run. Deletion/duplication indices 0–6 are already complete; do not
repeat them to claim new work. Do not run Python with {T}-O{T}.
""")
near=state(RUNS[-1][1]);remaining=near['candidates_total']-near['next_rank']
write('near-case-2026-09-30/README.md',f"""# Independently selected paragraph cases, 2026-09-30

**UNSOLVED.** The chapter writes {T}I STNM{T}, while its marked paragraphs
supply F,F,W,W initials and S,T,N,M endings. Earlier structured-twist searches
coupled the first and last letters of any added nearby paragraph
({T}calibrated-2026-09-28/twist-search.py:pattern_ops{T}). That does not cover
all independent choices of their ends. Arbitrary endpoint triples also do not
cover four or more changes outside the 32 marked endpoints.

## Completed

- **Nearby initials:** independently toggle the first letter of paragraphs
  3,8,9,91,164,165,166,233, on all 768 source-format bases. 196,608 candidate
  instances × indices 0–6 = **1,376,256** addresses, no match. Includes the
  plausible preceding {T}I{T} letters together and all subsets.
- **Every marked paragraph pair:** independently include/omit first+last
  changes for EACH of the 16 FFWW paragraphs. This is broader than choosing
  coherent whole groups. 65,536 masks × 48 formats = **3,145,728** candidates,
  **22,020,096** addresses, indices 0–6, no match.
  Some masks were covered by the prior radius-10 family; others were outside it.

Both are unfiltered, English/raw MD5/empty passphrase, compressed BIP44.
The rank-to-mask mapping for the second run was checked independently for all
65,536 masks. Source rebuilds, GPU MD5 and CPU wallet comparisons are recorded
in the checkpoints. Positive controls pass at startup.

## Broader next local run: first AND last independently

{T}search.py --endpoints both{T} selects both ends of the same eight nearby
paragraphs independently (16 bits), while preserving the coherent FFWW-group
selection in each of 768 bases. All 2¹⁶ masks are allowed, not a radius cutoff.
No spelling changes or voice/title motifs are added.

The benchmark checked **{near['next_rank']:,} / {near['candidates_total']:,}**
candidate/address operations at index 0, zero matches, **PARTIAL**.
**{remaining:,} remain.** It took {near['elapsed_search_seconds']:.1f}s,
about {near['next_rank']/near['elapsed_search_seconds']:,.0f}/s while other
GPU runs shared the device. Plan **20–40 minutes** on this machine; use the
live estimate. This is a tested, bounded hypothesis, not a guaranteed solution.

{T*3}powershell
{NEXT}
{T*3}

A separate invocation demonstrably resumed from 262,144 to 278,528, checking
16,384 further candidates in about 0.5s. It loaded the existing fingerprint
and saved additional progress successfully.

This resumes {T}near-both-6555be4d17950571.json{T}. {T}--limit N{T} limits
additional candidates; omit it for completion. Ctrl+C may repeat an unsaved
batch. Code/source/kernel fingerprints, atomic JSON saves and an OS lock
protect resume identity. A full address match must pass CPU reconstruction
and derivation before exact bytes and keys are saved locally.

The script-policy problem is avoided by invoking Python directly.
This run includes many overlaps with prior endpoint sweeps and the completed
initials run; counts are operations, not unique wallets.
""")
motif=state(RUNS[5][1]);combined=state(RUNS[6][1])
write('case-motifs-2026-09-30/README.md',f"""# Intraword capitalization and nearby initials, 2026-09-30

**UNSOLVED.** The source contains unusual {T}ppM{T}, {T}VIrgin{T},
{T}BItcoin{T}, and explicit {T}BITcoin{T}/{T}AHScoin{T} labels. These supply
seven uppercase letters inside words at paragraphs 72,127,135,208.
The author demonstrated an internal {T}vOIce{T} change in solved Block 29.
These observable letters motivate a small case family without presuming
they are errors or instructions to normalize the entire chapter.

## Actual scope and results

1. Independently toggle the seven capitals, plus either/both known
   {T}vOIce{T} pairs (paragraphs 11/23), plus the whole {T}SECOND{T} title
   motif when the title is included. 524,288 instances across 768 bases;
   indices 0–6 = **3,670,016** addresses. **Complete, no match.**
2. {T}--mixed-only --near-initials{T}: independently choose all seven capitals
   AND the eight nearby initials, preserving each coherent FFWW baseline.
   2¹⁵ masks × 768 bases = **25,165,824** candidates at index 0.
   Current checkpoint: **{combined['next_rank']:,}**, complete={str(combined['complete']).lower()},
   matches={len(combined['matches'])}. The voice/title motifs are omitted in this run.

The union of a capitals-only negative and an initials-only negative does not
exclude their combinations; run 2 checks that gap. Every bit-mask group is
mapped back to original character locations and compared with an independent
rebuild. GPU MD5 is certified per base, every wallet batch is checked on CPU,
and solved Stage One/Grycoin Block 1 pass on startup. No prefix filter is used.

{T*3}powershell
& 'C:\\Users\\boomb\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' .\\case-motifs-2026-09-30\\search.py --mixed-only --near-initials --indices 0
{T*3}

Same arguments resume the configuration-fingerprinted checkpoint. Different
index lists or inclusion of the voice/title motifs define different runs;
they are not automatically covered by the result above.
""")
write('investigation-2026-09-30/README.md',f"""# Quizchain investigation, 2026-09-30

**UNSOLVED. No verified final answer or winning key recovered.**
This pass audited the supplied exhaustion inventory, checked actual source
differences, and tested additional finite families. All work is in
{T}C:\\Users\\boomb\\Downloads\\puzzle-investigation{T}. No external messages
or transactions were sent.

## Actual progress

Snapshot: {now}. Per-directory checkpoints carry exact configuration,
code/source/kernel identity, CPU verification counts and timestamps.

{table}

Counts overlap heavily; they are not a globally unique address count.
The superseded source prototype and slower single-edit pilot are not added.
Historical invalid GPU checkpoints remain excluded.

## Findings that change the next search

- The original Finney quote has {T}facinating{T}; chapter paragraph 233 has
  {T}fascinating{T}. Earlier public story parts also contain six wording and
  three whitespace differences. The documented source family checks every
  subset of these changes plus quote delimiters and complete earlier sections.
- A radius cutoff on 32 FFWW endpoints does not exhaust all paired selections
  of the 16 paragraphs. Likewise, extra nearby paragraphs flipped at both ends
  do not exhaust independently selected initials/ends. These are distinct
  coverage gaps even if most operations overlap older searches.
- {T}ppM{T}, {T}VIrgin{T}, {T}BItcoin{T} are conspicuous interior capitals.
  Correcting all three requires three arbitrary interior changes, outside the
  completed two-letter sweeps. The new motif and combined-initial tests do not
  assume they are mistakes; they try every independent selection.
- The example's completed FFWW ≤3 checkpoint has a stale {T}derived{T} counter.
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
- Historical {T}FOUND-block29.json{T} is present and ignored. No {T}FOUND{T}
  file matches either final prize target.
- A current Wattpad modification timestamp and a zero-result CDX query do not
  certify the exact July 2019 hash buffer or prove all historical copies absent.

## Next local run

The nearby first/last family is prepared, certified and benchmarked.
Only {near['next_rank']:,} of {near['candidates_total']:,} candidates are checked; **{remaining:,} remain**.
This extends case selection based on the chapter's wording, rather than
repeating a completed brute-force radius.

{T*3}powershell
{NEXT}
{T*3}

Plan 20–40 minutes here, subject to device load. The same command resumes.
There is no promise that this is the intended answer. For independent analysis,
use [../CLAUDE-PUZZLE-HANDOFF.md](../CLAUDE-PUZZLE-HANDOFF.md), and
[../EXHAUSTED-INVENTORY.md](../EXHAUSTED-INVENTORY.md) with actual bounds.

## Resume and publication validation

The recommended run demonstrably resumed from 262,144 to 278,528. New
checkpoint-fingerprinted runner sources are stored byte-for-byte through
per-directory Git attributes; newline normalization would otherwise alter
some recorded script hashes. {T}verify-publication.py{T} checks the saved
source identities and compares staged Python/OpenCL blobs with the exact
working files used by the jobs. Its recorded result is
{T}reproducibility-check.json{T}.

## Current chain evidence

The read-only mempool.space responses in
[../source-variants-2026-09-30/chain-recheck.json](../source-variants-2026-09-30/chain-recheck.json)
record 77,700,000 sats unspent at 2026-09-30 04:14:35 UTC, including
{T}outspend/1: spent=false{T}. This is an observed chain snapshot.
""")
# Correct rather than discard the supplied inventory's earlier finite-family tables.
inv=read('EXHAUSTED-INVENTORY.md')
inv=inv.replace('**Status: UNSOLVED. No winning key or answer recovered. No '+T+'FOUND-*'+T+' file exists.**',
 '**Status: UNSOLVED. No final-target key or answer recovered.** The solved historical Block 29 has an ignored local '+T+'FOUND-block29.json'+T+'; it is a positive control, not the final prize.')
inv=inv.replace('is fixed and independently verified by the\npositive controls below.','is independently verified on the\npositive controls below; its applicability to the final answer is a strong\nworking hypothesis, not proof of the final settings.')
a=inv.index("Block 29 is the strongest") if "Block 29 is the strongest" in inv else inv.index("Block 29 is a long-text positive");z=inv.index('\n---',a)
inv=inv[:a]+f"""Block 29 is a long-text positive control: LF, MD5, one paragraph per line,
and no material outside its specified answer/link. Its draft contains no
NBSP, so it does not calibrate NBSP handling. The NBSP→space hypothesis comes
separately from the author's public Abstract reposts and HTML double spaces.
The example's {T}7759227{T} prefix calibrates its raw LF text, not its unreproduced
claim buffer. The author's CRLF descriptions keep that final hypothesis open.
"""+inv[z:]
a=inv.index("The example claim buffer is") if "The example claim buffer is" in inv else inv.index("At index 0, the example claim");z=inv.index('\n---',a)
inv=inv[:a]+f"""At index 0, the example claim is outside ≤3 case changes from **FFWW**;
only ≤2 is excluded from the other three baselines. The original triple
checkpoint omitted the final 11,130 operations from its {T}derived{T} counter,
though its final flush was checked. That exact tail was independently replayed
without a match: {T}source-variants-2026-09-30/example-tail-recheck.json{T}.
"""+inv[z:]
inv=inv.replace('"Change only a couple of letters" = exactly two ASCII case toggles applied on', 'The two-toggle matrix interprets "a couple of letters" as two ASCII case toggles on')
inv=inv.replace('infeasible — so this is the practical frontier for the chapter case space.', 'infeasible as a uniform search. Structured case families can still be small.')
inv=inv.replace('modifyDate'+T+' 2019-07-23T23:12Z (the final version).','modifyDate'+T+' 2019-07-23T23:12Z (reported metadata, not proof of the hashed 2019 buffer).')
a=inv.index('## F. ')
inv=inv[:a]+f"""## F. New work, 2026-09-30

{table}

See {T}investigation-2026-09-30/results.json{T} and the four new family
directories. The source prototype and slow edit pilot are superseded and
overlap the completed authoritative runs.

## G. What remains open

More finite, feasible families still exist. Do not equate billions of overlapping
negative operations with proof that only unreachable brute force remains.

- Broader nearby first/last choices: {near['candidates_total']:,} at index 0, only {near['next_rank']:,} checked.
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
{T}near-case-2026-09-30/README.md{T}. No match is a negative for that exact
family only. {T}CLAUDE-PUZZLE-HANDOFF.md{T} gives the full public-puzzle context
without promising a solution or another service's policy classification.
"""
write('EXHAUSTED-INVENTORY.md',inv)
# Preserve the root README's detailed older chapters as history, replacing the stale lead.
r=read('README.md');a=r.index('## Evidence and confirmed method')
lead=f"""# Quizchain last block: reproducible investigation

Status on **2026-09-30: UNSOLVED**. No final answer or winning key was recovered.
Current public target: {T}14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W{T}.
The 04:14 UTC chain snapshot reports its 77,700,000-sat funding output unspent.

Read [investigation-2026-09-30/README.md](investigation-2026-09-30/README.md)
for the latest actual results, [EXHAUSTED-INVENTORY.md](EXHAUSTED-INVENTORY.md)
for the bounded negatives, and
[CLAUDE-PUZZLE-HANDOFF.md](CLAUDE-PUZZLE-HANDOFF.md) for independent review context.
The 28,194,048-candidate mixed-format family is now **complete, no match**;
old partial progress in dated reports is historical.

The new runs test actual earlier-source wording, a one-character copying
difference, independent nearby initials/ends, independent marked paragraph
pairs, and unusual interior capitalization. These differ from merely repeating
the exhausted endpoint-radius commands. Detailed scopes and checksums are in
their directories. Counts overlap and do not imply exhaustive coverage.

The broadest remaining prepared nearby-endpoint run has **{remaining:,}**
candidates left after a verified pilot. Invoke Python directly, avoiding
PowerShell script-policy restrictions:

{T*3}powershell
{NEXT}
{T*3}

Budget roughly 20–40 minutes on the tested RTX 4060. It resumes automatically;
this is a bounded hypothesis, not a recovered clue or guaranteed solution.

"""
write('README.md',lead+r[a:])
# Update the independent-investigator prompt and remove the stale preferred mixed-format run.
h=read('CLAUDE-PUZZLE-HANDOFF.md')
a=h.index('Read '+T+'audit-2026-09-28/README.md'+T) if 'Read '+T+'audit-2026-09-28/README.md'+T in h else h.index('Read '+T+'investigation-2026-09-30/README.md'+T);z=h.index('\n## Public challenge',a)
h=h[:a]+f"""Read {T}investigation-2026-09-30/README.md{T} and
{T}EXHAUSTED-INVENTORY.md{T} first. The 28,194,048-candidate mixed-format
run is now complete with zero matches; old 8,962,048 notes are historical.
The 2026-09-30 pass adds actual wording differences, complete one-ASCII-edit
coverage on six bases, independent nearby initials and all marked paragraph
pairs, plus unusual-capitalization tests. Exact settings/results are below.
No final-target match has been recovered.
"""+h[z:]
a=h.index('## New bounded run prepared after those negatives') if '## New bounded run prepared after those negatives' in h else h.index('## Actual additional tests, 2026-09-30');z=h.index('## What I want from you',a)
h=h[:a]+f"""## Actual additional tests, 2026-09-30

{table}

These counts are overlapping operations, not unique addresses. Read the actual
checkpoint and the family README; do not promote the 262,144 nearby-endpoint
pilot to a completed 50-million-candidate negative.

Primary-source differences:
{T}source-variants-2026-09-30/README.md{T} documents six earlier wordings,
three whitespace differences and the Finney spelling {T}facinating{T} versus
chapter {T}fascinating{T}. The family also tries quote delimiters and whole
earlier sections. It does not guess arbitrary historical prose.

Human-scale case gaps:
The old structured-twist runner couples both ends of extra paragraphs. The
new tests distinguish independently selecting their initial {T}I{T} letters
({T}I STNM{T}) and independently including each of the 16 marked paragraph
pairs. Radius 10 around 32 endpoints is not the full paired-paragraph space.
Seven unusual interior uppercase letters and the documented voice/title
motifs supply another finite family. Their combinations are explicitly labeled.

Audit corrections:
Block 29 is now a reproduced long-text positive control, MD5
{T}982301b80b30af3a0abe110269b0dd43{T} with link {T}zff{T}, LF draft,
funded address {T}1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P{T}; WIF suffix
{T}JRu{T} agrees with the next block's published link.
It contains no NBSP and cannot prove NBSP handling in the final chapter.
Only the FFWW example baseline has completed unfiltered ≤3 case coverage;
other baselines have ≤2. A separate 11,130-tail replay resolves its stale
derived counter without rewriting the original checkpoint.

## Prepared next command

The broader nearby-endpoint family independently toggles both ends of eight
nearby paragraphs on 768 coherent FFWW/serializer/start/tail bases. It has
**{remaining:,} untested candidates** after the partial pilot, index 0, raw MD5,
English BIP39, empty passphrase, both final targets, no prefix filter.

{T*3}powershell
{NEXT}
{T*3}

The initial 262,144 took 10.7 seconds with shared GPU load. Plan 20–40 minutes,
then use the live estimate. Same arguments resume automatically. Hash-prefix
matches are insufficient; every address hit requires CPU reconstruction.
Further source analysis may have higher value than simply increasing a count.

"""+h[z:]
h=h.replace('| New mixed-format run and actual pilot status |','| Completed mixed-format run and recovery history |')
maprow='| Latest additional runs and limits | '+T+'investigation-2026-09-30/README.md'+T+', '+T+'EXHAUSTED-INVENTORY.md'+T+', '+T+'source-variants-2026-09-30/'+T+', '+T+'single-edit-2026-09-30/'+T+', '+T+'near-case-2026-09-30/'+T+', '+T+'case-motifs-2026-09-30/'+T+' |'
if maprow not in h:h=h.replace('| Purpose | Files |\n| --- | --- |','| Purpose | Files |\n| --- | --- |\n'+maprow)
write('CLAUDE-PUZZLE-HANDOFF.md',h)
# Mark the old pilot/recovery prose historical while retaining its evidence.
j=read('joint-format-2026-09-28/README.md')
banner="""<!-- current-completion -->
**Current status, 2026-09-30: COMPLETE, no match.** The authoritative checkpoint
checks all **28,194,048** candidate/address operations, index 0, with 5,163
sampled CPU comparisons and 3,285.234 recorded search seconds.
The 8,962,048 recovery milestone below is historical, not the current remaining
work. The pilot/recovery sections preserve how progress was recovered.
<!-- /current-completion -->

"""
j=re.sub(r'<!-- current-completion -->[\s\S]*?<!-- /current-completion -->\n\n','',j)
k=j.index('\n')+1;j=j[:k]+'\n'+banner+j[k:].lstrip('\n')
j=j.replace('## Actual pilot and runtime','## Original pilot and runtime (historical)').replace('## Windows checkpoint failure and recovered progress','## Windows checkpoint failure and recovered progress (historical)')
write('joint-format-2026-09-28/README.md',j)
e=read('example-crack-2026-09-29/README.md')
e=e.replace('| ffww-quad | ≤3 | 285,846,394 | 0 | running |','| ffww-quad | ≤3 | 285,846,394 | 0 | complete, no match |')
e=re.sub(r'So the example claim buffer is[\s\S]*?(?=\n'+re.escape(T*3+'powershell')+')',f"""At index 0, ≤3 is excluded from FFWW, and ≤2 from the other three baselines.
Do not infer ≥4 from every baseline. The final derived counter was stale by
11,130; the code did flush/check that tail. A separate independent replay
also found no match, recorded in
{T}../source-variants-2026-09-30/example-tail-recheck.json{T}.
""",e)
write('example-crack-2026-09-29/README.md',e)
ignore=read('.gitignore')
for pattern in ['source-variants-2026-09-30/*.lock','single-edit-2026-09-30/*.lock','near-case-2026-09-30/*.lock','case-motifs-2026-09-30/*.lock',
 '*/*.json.pending-*.tmp','source-variants-2026-09-30/source-variants-e92eaa4a6a257540.json']:
 if pattern not in ignore.splitlines():ignore+='\n'+pattern
write('.gitignore',ignore)
print(json.dumps(dict(updated_utc=now,records=[dict(name=r['name'],checked=r['checked'],total=r['total'],complete=r['complete']) for r in records])))
