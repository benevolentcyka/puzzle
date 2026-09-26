# Quizchain last block: reproducible investigation

Status on 2026-09-26: **unsolved**. This repository preserves the
evidence and bounded searches performed so far; it contains no winning key.
The current prize address is
`14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W`. The public Bitcoin API reports one
funded output of 77,700,000 sats and no spends. The funding transaction is
`a1916e7ed9eac3fcc56a55056328cb09d06925e2694f2e6720de12b228514d1f`,
output 1. The original `1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC` was superseded.

## Evidence and confirmed method

- Original puzzle post and revision: <https://www.reddit.com/r/Grycoin/comments/cgkpbb/777_mbtc_quizchain_last_block/>
- Author's clarification that final paragraph separators are two CRLFs
  (bytes 13,10,13,10): <https://www.reddit.com/r/Grycoin/comments/chn8un/real_big_block_discussion/>
- Chapter: <https://www.wattpad.com/720888559-second>.
  Public text API: <https://www.wattpad.com/apiv2/?m=storytext&id=720888559>.
  Public metadata API: <https://www.wattpad.com/api/v3/stories/184148284?fields=parts(id,title,modifyDate,publishDate)>.
  Wattpad reports this part's modification date as `2019-07-23T23:12:04Z`,
  before replacement funding on 2019-07-30.
- Source for solved first stage: <https://bitcointalk.org/index.php?topic=155054.0>.
  The source's 16 paragraphs, with the first/last letter case change applied
  to the four whose initials are outside `ITASM`, joined with `\n\n` and no
  trailing newline, yield MD5 `9dd2efb9bc976c2095bd534d7b8d431c`.
  BIP39/BIP44 path `m/44'/0'/0'/0/0` gives its known claimed address
  `19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN`. Run
  `node .\verify-stage-one.cjs` to reproduce this.
- Independent derivation code: `verifier.cjs`. Run
  `node .\verifier.cjs --selftest`. It reproduces the author's
  published WIF vector for entropy `2941774a2abec9f30c7d6777d1d53d91`
  at BIP44 index 1, as well as the solved first-stage address. It uses MD5
  of exact UTF-8 bytes, BIP39 12 words, empty passphrase, BIP44 and compressed
  P2PKH. `--file PATH` hashes an exact candidate file.

## Recovered chapter and checks

`wattpad-api-720888559.txt` is the public Wattpad text response.
`wattpad-paragraphs.json` extracts its 273 paragraphs, retaining text and
spaces. `wattpad-paragraph-audit.json` records checks of the Wattpad `data-p-id`
MD5 against each paragraph. 272 of 273 text values match directly or under
documented whitespace/newline variants. The one mismatch is paragraph 77,
the **second** occurrence of `"What?"`. A control check of Wattpad part
720895205 found that all 147 repeated paragraph occurrences there receive
distinct non-MD5 IDs while every first occurrence matches its text MD5.
This explains paragraph 77 as Wattpad duplicate-ID disambiguation; it is
not evidence of a historical edit. Run
`python .\verify-wattpad-ids.py` to reproduce these counts from
the two saved API responses; `wattpad-id-control.json` records the result.

The chapter contains planted groups of F,F,W,W paragraphs and discusses the
same paragraph-initial clue as the solved first stage. Aoi later explicitly
said the format in **both** stages keeps the whole text and changes only
selected letters' capitalization; see
<https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/>.
The exact letter selection and final bytes are still unproven.

I downloaded and searched the available public history of Aoi's account:
202 posts and 864 comments. See `AUTHOR_AUDIT.md` and
`aoi-posts-archive.json` / `aoi-comments-archive.json`. The later format
example has a published raw MD5 prefix `7759227`; the archived question
reproduces that prefix with `\n\n`, but not `\r\n\r\n`. This is a concrete
reason to keep both line-ending hypotheses open despite Aoi's description.
`mini-format-test.py` checks that example's payout under zero to two case
toggles and BIP44 indices 0–6, with no match.

## New targeted test

The [solved Quizchain Block 2](https://www.reddit.com/r/bitcoinpuzzles/comments/bnj24w/77_mbtc_quizchain2_block_2/en6e73r/)
used a further MD5 of a derived WIF, so
`nested-wif-search.cjs` checks whether the final puzzle repeats that pattern.
It generates 292 unique chapter variants from full text, section ranges,
candidate F,F,W,W case changes, LF versus CRLF pairs, terminal newlines, and
NBSP handling. It checks their direct addresses at indices 0–6 and then a
second MD5/BIP39/BIP44 stage using each derived WIF, address and private-key
hex, as well as each first-stage mnemonic and entropy hex. That is 49,056
derived addresses in all. `nested-results.json` records **zero matches** for
both the current and superseded prize addresses.

I also checked a direct continuation from the solved first-stage wallet:
indices 0–9, with each WIF, address and private-key hex rehashed into a second
wallet, plus the first-stage mnemonic and entropy hex (224 derived addresses).
There was no match.

This is only a bounded family. A missing text edit, a different paragraph
selection, or an older copy of the chapter could change the MD5 completely.
Public research at
<https://github.com/floflo777/open-crypto-puzzles/blob/main/1-big-prizes/aoi-nakamoto-quizchain-0-854btc/README.md>
reports far larger negative searches, but those do not prove that the prize
cannot be solved.

## Follow-up, 2026-09-25

See `followup-2026-09-25/FINDINGS.md`. It is still unsolved. The main new points:

- Aoi reported using a tablet (her Wattpad part "Mistakes"). The reproduced
  example hash supports LF bytes directly; the tablet is a possible
  explanation, and does not establish her exact editing or hashing workflow.
- The Grycoin Block 2 format example was solved by puzzleponky. Stage One fell
  to the same sweep address seven minutes later. That example is therefore the
  useful calibration target. About 621 million reported variants were tested,
  including every combination of up to three extra toggles. Those negatives
  apply to the tested derivation settings; they do not exclude a tool mismatch.
- The main chapter families were rechecked at BIP44 indices 0–20 (the public
  ledger used 0–5), with new families: `<br>` promotion, the author's
  "letter in Satoshi" wording, stripped spaces, truncation, twist repertoire,
  and non-BIP44 paths. None matched.

## Follow-up, 2026-09-26

See `followup-2026-09-26/FINDINGS.md` for corrected evidence, new exact-byte
searches, and their result records. Two reproducibility fixes matter:
`.gitattributes` preserves the distinct LF/CRLF byte files, and the earlier
`brPromote` generator now avoids inserting an extra CR before every CRLF.
Run `node .\verify-search-inputs.cjs` before resuming a saved GPU checkpoint.

## Local GPU computation

`make-search-bases.py` builds six exact-byte full-chapter hypotheses from the
saved Wattpad text: no F,F,W,W group flips, first three groups flipped, or all
four groups flipped; each with LF LF or CRLF CRLF between paragraphs. Each
file has 35,825 ASCII letters, giving 641,697,400 distinct pairs of two
additional case toggles. This is a bounded extension beyond the public
search ledger's single-edit and paragraph-boundary two-edit tests. It does
not include arbitrary character replacements, changed paragraph selection,
or a different BIP39 derivation path.

From the repository root on Windows, with Python 3.12+, Node.js, an OpenCL
driver, and Git installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
.\setup-gpu.ps1
python .\gpu-probe.py 4096
python .\make-search-bases.py
node .\verify-search-inputs.cjs
python .\gpu-case-pairs.py --base .\bases\four-groups-lflf.txt --limit 1000000
```

The last command resumes from its own base/index checkpoint on each run.
To exhaust a base, run:

```powershell
python .\gpu-case-pairs.py --base .\bases\four-groups-lflf.txt --all
```

Replace the base filename with `four-groups-crlfcrlf.txt`,
`three-groups-lflf.txt`, `three-groups-crlfcrlf.txt`, `raw-lflf.txt`, or
`raw-crlfcrlf.txt` to test the other hypotheses. Use `--index 1` (and further
indices) only after index 0 if there is a reason to test another address in
the BIP44 wallet. Checkpoints are base/index-specific JSON files in this
directory. `--start N` overrides a checkpoint when a precise pair range is
needed. A confirmed match writes `FOUND-*.txt` and `FOUND-*.json` with the
exact answer bytes and mnemonic; keep those files private if created.

The setup script clones and locally patches
<https://github.com/AlexMelanFromRingo/BIP39-GPU> at commit
`08f189d3ade6a18e18acc82f18a7bfb576c6e86f`. The patch is saved in
`patches/bip39-gpu-fixes.patch`; the upstream library itself is not committed.
The only two local fixes
add its missing kernel loader and correct the OpenCL PBKDF2 password address
space. GPU fallback is disabled in `gpu-case-pairs.py`; the program checks
five OpenCL outputs against independent CPU BIP39/BIP44 results at startup,
including the known Stage One wallet, and checks incremental MD5 pair
generation against direct hashing. Required Python packages on a fresh local
environment are `numpy`, `pyopencl`, `bip_utils`, and `ecdsa`.

On the available RTX 4060 Laptop GPU, a 65,536-candidate batch runs at about
21,000–24,000 pairs/second. A complete 642-million-pair sweep of **one**
base may take around eight hours. As of this report, `four-groups-lflf.txt`
has been checked through pair rank 320,065,408 (snapshot at 2026-09-26 08:43 UTC) and
`four-groups-crlfcrlf.txt` through 1,104,096, without a match. The respective
checkpoint files record the exact next ranks. Neither constitutes a completed
negative result for its entire family. A separate pre-existing process continues
the LF run in the original local checkout; do not start a competing copy on the
same GPU. After that run finishes, `run-gpu-sweep.ps1` resumes and runs all six
bases sequentially. Copy its latest matching checkpoint first if using a newer
checkout. The six bases preserve internal LF breaks even when paragraph joins
are CRLF pairs; the canonical CRLF internal-break hypotheses are tested in the
September 26 searches.

The OpenCL platform defaults to `1`, which selected the NVIDIA card on the
investigation machine. On another machine, pass `--platform N` to
`gpu-case-pairs.py` after identifying its OpenCL platform. Do not commit or
publish a future `FOUND-*` file: it would contain the spendable private key.

The most useful new evidence would be a byte-preserving browser copy or editor
buffer of the "Second" chapter as it stood in July 2019, or a precise clue to
which paragraphs the author copied and changed. The Wattpad modification date
supports the current text as an early snapshot, but it does not establish the
exact bytes fed to the author's hash tool.
