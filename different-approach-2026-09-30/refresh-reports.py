"""Publish actual new-family checkpoint results and retire stale recommendations."""
import datetime
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
T='`'
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
NEXT="""Set-Location 'C:\\Users\\boomb\\Downloads\\puzzle-investigation'
& 'C:\\Users\\boomb\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' .\\different-approach-2026-09-30\\chapter-signatures.py --i-styles remaining --group-masks 15,7 --platform 1"""


def write(path,text):
    (ROOT/path).write_bytes(text.replace('\r\n','\n').encode('utf8'))


def read(path):
    return (ROOT/path).read_text(encoding='utf8')


records=[]
for path in sorted(HERE.glob('*.json')):
    if path.name=='chapter-sections-c9f7df2cab214926.json' or '-plan-' in path.name:
        continue
    s=json.loads(path.read_bytes())
    c=s.get('configuration',{})
    if c.get('family') not in ['independent-section-clipboard-policies-v1','i-stnm-independent-section-layouts-v1','joint-example-layout-case-v1']:
        continue
    assert 0<=s['next_rank']<=s['candidates_total']
    assert s['complete']==(s['next_rank']==s['candidates_total'])
    for file,wanted in c['source_sha256'].items():
        assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==wanted,(path.name,file)
    if c['family']=='independent-section-clipboard-policies-v1':
        name='Chapter: independent formatting in three sections, voice retained/vOIce'
    elif c['family']=='i-stnm-independent-section-layouts-v1':
        style_names=list(c['styles'])
        style_label=','.join(style_names) if len(style_names)<=3 else f'{len(style_names)} remaining selections'
        name='Chapter: I-STNM signatures '+style_label+', group masks '+','.join(map(str,c['masks']))
        plan=HERE/f'chapter-signatures-plan-{path.stem.split("-")[-1]}.json'
        p=json.loads(plan.read_bytes())
        assert p['configuration']==c and p['candidates_total']==s['candidates_total']
        assert hashlib.sha256(json.dumps(p['bases'],sort_keys=True).encode()).hexdigest()==c['manifest_sha256']
    else:
        name=f"Example: {c['layout_family']}, {c['defects']} defect(s), {c['case_mode']} case choices, prefix {c['filter']}"
    records.append(dict(name=name,path=str(path.relative_to(ROOT)).replace('\\','/'),
        checkpoint_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),checked=s['next_rank'],total=s['candidates_total'],
        derived_entropies=s.get('derived_entropies',s['next_rank']),addresses=s['derived_addresses'],
        complete=s['complete'],matches=len(s['matches']),elapsed_seconds=s['elapsed_seconds'],
        sampled_cpu_comparisons=s['sampled_cpu_comparisons'],source_identity_verified=True))
table='| Family | Text operations checked / total | Address operations | Status |\n| --- | ---: | ---: | --- |\n'
for r in records:
    status=('COMPLETE' if r['complete'] else 'PARTIAL')+f", {r['matches']} matches"
    table+=f"| {r['name']} | {r['checked']:,} / {r['total']:,} | {r['addresses']:,} | {status} |\n"
(HERE/'results.json').write_bytes((json.dumps(dict(updated_utc=NOW,runs=records),indent=2)+'\n').encode())
source=json.loads((HERE/'source-audit.json').read_bytes())
chain=json.loads((HERE/'public-recheck.json').read_bytes())
snapshot=chain['checked_utc']
next_total=29_393_280
next_addresses=next_total*7
next_record=next(r for r in records if r['path'].endswith('chapter-signatures-c4bf1d67bc62879a.json'))
next_checked=next_record['checked']
next_remaining=next_total-next_checked
pilot=f'The exact command has checked **{next_checked:,} / {next_total:,}** candidates, with zero matches.\nIt successfully resumed from rank 32,768 to 65,536; **{next_remaining:,} remain**.'
report=f"""# A different approach after the nearby-endpoint negative

**UNSOLVED. No final answer or winning key recovered.** Snapshot: {NOW}.
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
The chapter explicitly combines an {T}I{T} with {T}STNM{T} (paragraphs 237–238).
The nearby {T}I{T} paragraphs are 3, 91, 164, 165, 166, 233. Selecting their
initials had already been searched on global serializer bases; the new work
crosses those selections with independently formatted sections. This is a
clue-based hypothesis, not a claim that these are the intended extra letters.

The claimed Grycoin Block 2 example remains a useful calibration target.
Its published raw-question prefix {T}7759227{T} reproduces, but its claim buffer
does not. Its reference to a paragraph ending in {T}himself{T} conflicts with
the following sentence in that paragraph. Prior removed/split-sentence and
case-only searches already address that mismatch; it is not a newly found clue.
The new example runner combines case choices AND clipboard defects together.

## Actual new results

{table}
Counts are operations, with overlap; do not sum them as unique wallets.
For the example, {T}3c6{T} is an explicit MD5 filter. Only surviving digests
are derived. The chapter runs have **no prefix filter** and check both final
escrows at compressed BIP44 indices 0–6, raw MD5, English BIP39 and empty
passphrase. The two hashes/settings are working hypotheses for the final.

## Best next local run

{T*3}powershell
{NEXT}
{T*3}

This searches the other **60 nonempty subsets of the six nearby I initials**
with the two strongest FFWW interpretations: all four groups ({T}15{T}),
or the first three excluding the quoted Stage One group ({T}7{T}).
Each is crossed with independent section policies and {T}voice{T}/{T}vOIce{T}.
Total: **{next_total:,} entropy candidates / {next_addresses:,} address operations**.
{pilot}
It reuses the corrected GPU dependency already installed on this machine.
It invokes Python directly, so the PowerShell execution-policy error does not apply.

Budget approximately **45–90 minutes** on the measured RTX 4060 laptop, with
more time under load. Startup builds and verifies its source/layout plan before
GPU progress appears. The same command resumes its own fingerprinted checkpoint.
For a short initial run, append {T}--limit 32768{T}; remove it to continue.

An optional broader version removes {T}--group-masks 15,7{T}, keeping all
16 group selections: **235,146,240 entropy candidates / 1,646,023,680 addresses**,
roughly **5–10 hours** here. The previous default first/nearest/all I signatures
are excluded by {T}--i-styles remaining{T}. This still does not exhaust arbitrary
source bytes, case patterns or derivation settings.

## Exact formatting choices

Sections are paragraphs 0–86, 87–161 and 162–272. Each independently chooses:

- Embedded line breaks: retain LF, match the global platform, promote to a
  paragraph separator, replace with a space, or remove.
- Paragraph/pre-embedded-break spaces: keep or trim.
- NBSPs: keep, replace with ordinary space, or remove. Section I has none.
- Section I only: keep {T}voice{T} or use the previously solved {T}vOIce{T}.

The global paragraph separator stays uniformly LF LF or CRLF CRLF. Starts
0/1/3 and no terminal newline / LF / CRLF are included. Byte-identical section
options are deduplicated before enumeration. Neither paragraph words nor
their ordering are guessed. The returned exact policy is sufficient to
reconstruct a candidate.

## All-source comparison and current primary evidence

{T}source-audit.py{T} checks the SHA256 and byte count of all 33 saved Wattpad
parts, including the current chapter, then compares the other 32 parts and
the author's 202 archived posts / 864 comments. It compared
**{source['normalized_corpus_paragraphs']:,} distinct normalized paragraphs**
with a declared similarity threshold 0.88. All additional close matches were
already tested earlier wordings or a Reddit {T}Hint two:{T} preface to an
otherwise exact quote. It found no additional close draft wording. Whitespace
is normalized for this audit; it does not exclude differently formatted or
more heavily rewritten historical text.

{T}public-recheck.json{T} records a fresh read-only snapshot at {snapshot}:
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
checked against {T}hashlib.md5{T}, and calibrated byte-for-byte to the saved
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

Checkpoint files and {T}results.json{T} carry real progress. The static
{T}chapter-signatures-plan-*.json{T} stores the full plan once, keeping each
atomic progress write small. Private {T}FOUND-*{T} files remain ignored.
"""
write('different-approach-2026-09-30/README.md',report)
# Retire the former next-run paragraph, preserving older evidence chapters.
root=read('README.md')
start=root.index('## Evidence and confirmed method')
lead=f"""# Quizchain last block: reproducible investigation

**2026-09-30: UNSOLVED. No final-target answer or key recovered.**
Target: {T}14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W{T}; its funding output was
still unspent at {snapshot} (77,700,000 sats).

The nearby first/last family is complete: **50,331,648 candidates, zero matches**.
The new work compares all saved author sources and crosses clue-based case
selections with independently formatted chapter sections. Read
[the new report](different-approach-2026-09-30/README.md),
[the complete bounded inventory](EXHAUSTED-INVENTORY.md), and
[the Claude handoff](CLAUDE-PUZZLE-HANDOFF.md).

Best next local run, approximately 45–90 minutes on the tested RTX 4060:

{T*3}powershell
{NEXT}
{T*3}

**29,393,280 entropy candidates / 205,752,960 addresses**, no MD5 hint filter.
It combines the other 60 nearby-I subsets with section-specific formatting,
all-four/first-three FFWW selections and the earlier {T}vOIce{T} motif.
It resumes automatically and calls Python directly. This is a tested finite
hypothesis, not a guarantee of a solution. All counts are overlapping operations.

"""
write('README.md',lead+root[start:])
inv=read('EXHAUSTED-INVENTORY.md')
inv=re.sub(r'- Broader nearby first/last choices:[^\n]*\n','',inv)
inv=inv.replace('The latest commands and benchmark are in\n'+T+'near-case-2026-09-30/README.md'+T,
                'The latest commands and benchmark are in\n'+T+'different-approach-2026-09-30/README.md'+T)
inv=inv.split('\n## H. Combined section formatting and I signatures')[0]
inv+=f"""
## H. Combined section formatting and I signatures

Snapshot {NOW}. The earlier nearby-endpoint run is actually complete,
50,331,648 candidates, zero matches.

{table}
The example row filters {T}3c6{T}; chapter rows have no prefix filter. Counts
overlap all previous work. Source comparison across all 33 Wattpad parts plus
202 posts and 864 comments found no additional close draft wording at its
specified 0.88 threshold. See {T}different-approach-2026-09-30/source-audit.json{T}.
The other 60 I subsets on independently formatted sections form the next
finite family: 29,393,280 candidates at group masks 15/7, indices 0–6.
{pilot}
"""
write('EXHAUSTED-INVENTORY.md',inv)
handoff=read('CLAUDE-PUZZLE-HANDOFF.md')
handoff=handoff.split('\n## Later combined-layout investigation, 2026-09-30')[0]
handoff=handoff.replace("The user's latest completed run is real, not hypothetical:",
                        "The user's September 28 completed run is real, not hypothetical:")
handoff=re.sub(r'These counts are overlapping operations, not unique addresses\. Read the actual\ncheckpoint and the family README; do not promote[^\n]*\npilot to a completed 50-million-candidate negative\.',
    'These are overlapping operations, not unique addresses. The nearby first/last\nfamily now actually completed all 50,331,648 candidates with no match.',handoff)
prepared=f"""## Prepared next command

The nearby first/last endpoint family is now exhausted at 50,331,648 candidates.
Use this subsequent I-signature and independent-section-layout family:

{T*3}powershell
{NEXT}
{T*3}

{pilot}
It checks both final targets at indices 0–6, raw MD5/English BIP39/empty
passphrase, with no prefix filter. Plan approximately 45–90 minutes here.
Same arguments resume automatically. The later section below explains
the hypothesis and exact new coverage. Every address hit requires CPU
reconstruction; a matching hash prefix alone is insufficient.

"""
handoff=re.sub(r'## Prepared next command\n[\s\S]*?(?=## What I want from you)',prepared.replace('\\','\\\\'),handoff)
new_map='| Latest combined-layout results and source comparison | '+T+'different-approach-2026-09-30/README.md'+T+', '+T+'results.json'+T+', '+T+'source-audit.json'+T+' |'
if new_map not in handoff:
    handoff=handoff.replace('| Purpose | Files |\n| --- | --- |','| Purpose | Files |\n| --- | --- |\n'+new_map)
handoff+=f"""
## Later combined-layout investigation, 2026-09-30

Read {T}different-approach-2026-09-30/README.md{T} and its results/plan files.
The user's nearby-endpoint job is actually complete, no match. The new family
independently applies embedded-break, NBSP and trailing-space policies in
each of the three chapter sections, crossed with FFWW selections and the
published {T}vOIce{T} motif. This can change many formatting sites together.
It is broader than global serializers or two/three isolated site edits.

{table}
The signature variants lowercase nearby initial I bytes at:
first = [3,91,164,233]; nearest = [3,91,166,233]; all = [3,91,164,165,166,233].
The next prepared family tests the other 60 nonempty subsets of those six I
locations on group masks 15/7: 29,393,280 buffers / 205,752,960 addresses,
English/raw MD5/empty passphrase/BIP44 indices 0–6, both escrows, no hint filter.
{pilot}
The full all-16-group version is 235,146,240 / 1,646,023,680; it remains finite.

All 33 saved Wattpad parts were fingerprint-verified and compared against the
current chapter, plus 202 posts and 864 comments (2,983 unique normalized
paragraphs). No additional close draft wording beyond the already tested
differences was found at the declared 0.88 threshold. This is not an exhaustive
historical-text archive. Raw example {T}7759227{T} still matches; its solution
{T}3c6{T} digest/key remains unreproduced. Solving that calibration example
could still clarify the final input workflow.

Please reason from the primary clues and actual negative bounds. Look for
an untested coherent rule or independently recoverable historical input,
and explain why it predicts particular bytes. Do not relabel an exhausted
radius or globally normalized buffer as a new approach. A local verifier and
reproducible finite family are useful even if no winning match is found.
"""
write('CLAUDE-PUZZLE-HANDOFF.md',handoff)
# Keep the earlier dated report's tables, but replace its exhausted command.
old=read('investigation-2026-09-30/README.md')
a=old.index('## Next local run')
z=old.index('## Resume and publication validation',a)
old=old[:a]+f"""## Next local run

The nearby-endpoint family now actually completed all 50,331,648 candidates,
with zero matches. Its former recommendation is retired. See
[the subsequent combined-layout investigation](../different-approach-2026-09-30/README.md)
for the next tested command and actual coverage.

"""+old[z:]
write('investigation-2026-09-30/README.md',old)
near=read('near-case-2026-09-30/README.md')
near=near.replace('## Broader next local run: first AND last independently',
                  '## Completed broader run: first AND last independently')
near=near.replace('zero matches, **PARTIAL**.','zero matches, **COMPLETE**.')
if 'The former next-run recommendation is retired.' not in near:
    near+='\nThe former next-run recommendation is retired. See\n[the combined-layout investigation](../different-approach-2026-09-30/README.md)\nfor the new command and coverage. The command above reproduces a completed negative.\n'
write('near-case-2026-09-30/README.md',near)
print(json.dumps(dict(updated_utc=NOW,new_run_records=len(records),next_candidates=next_total,next_addresses=next_addresses)))
