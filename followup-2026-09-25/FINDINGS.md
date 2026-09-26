# Follow-up, 2026-09-25/26: new evidence and new negatives

Status: **still unsolved.** No key was found. The 0.777 BTC output at
`14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W` was still unspent when checked on
2026-09-25. This folder records what was learned and ruled out, so nobody repeats it.

**Audit correction, 2026-09-26:** the reported `brPromote` CRLF branch originally
introduced extra CR bytes and did not test its intended serialization. It is
fixed and independently rerun in `../followup-2026-09-26/verification/`.
Also, tablet use does not prove LF handling, and spending a stored WIF does not
prove the author retained the source text. The revisions below distinguish
those inferences from established evidence.

Run `node example-block-search.cjs` and `node chapter-variants.cjs` to reproduce
the negatives below. Both scripts first self-test against the solved Stage One
address and the solved Grycoin Block 1 address.

## New evidence

1. **Aoi hashed on a tablet.** In the Wattpad part
   [Mistakes](https://www.wattpad.com/724275249-second-mistakes) she writes: "I restarted
   my tablet and the hashing tool I use switched back to the default (MD5)." Tablet use is
   established; the proposed explanation for LF bytes, autocorrect, and touch-selection
   artifacts remains a hypothesis. The reproduced example MD5 supplies the direct LF
   evidence, independently of that device inference.
2. **The format example was solved from public information.** Grycoin Block 2
   ([cleczc](https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/)) paid
   `1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi`. It was swept at 2019-08-03 14:02 UTC to
   `129jw1GUGwiJbf4rL7qEANPbxvSRC5zfHN`, and Stage One was swept to the same address
   **7 minutes later** (14:09). That address collected about 30 Quizchain prizes from
   2019-04-13 onward. It belongs to the prolific solver puzzleponky, not to Aoi. So one
   insight from the example unlocked Stage One immediately. puzzleponky never published it.
3. **Aoi could spend the original escrow after her lost-information statement.** The superseded escrow
   `1EFojc…` was swept on 2019-07-30 23:40 to `36nwcMJwoy99xyENeRcCCQmA3FZibji3Un`. That
   exact output (77,690,300 sats) funded the example block on 2019-08-01, two days before
   she posted it. This establishes access to a signing key on July 30. It does not establish
   that the original answer text or hash was retained, and does not refute the lost-information
   statement in *Starting Up* (whose API modifyDate is July 23).
4. **Grycoin chain calibration.** MD5("Still 21st Century"), the published Grycoin Block 1
   answer, derives `18EpYz5qB3XoxZWouJF3KdEp3E2nfv9FgP` at `m/44'/0'/0'/0/0`, which is that
   block's funded output. The Grycoin chain therefore uses the same MD5 → BIP39 → BIP44
   index 0 pipeline.
5. **Two wordings of the sign letters.** On 2019-07-28
   ([comment](https://www.reddit.com/r/Grycoin/comments/civj2n/comment/evas55t/)) Aoi
   wrote "all the paragraphs not starting with a letter in 'Satoshi'" (S A T O H I). The
   chapter lists "I, T, A, S, and M".
6. **Mid-sentence hard breaks are a device artefact.** They recur in her Reddit posts at
   about 78–83 characters and in the chapter at 107–111 (`one bullet to \nthe brain`). So the
   chapter's 10 internal `<br>` are real line breaks from her source, not Wattpad damage.
7. **The split bold heading is benign.** `<b>b) THOMAS and Satosh</b><b>i</b>` (unique
   across all 33 parts) and `<b>c) BITcoin is actually AHScoin</b> ` fit manual bolding with
   touch-selection handles that miss the last character. They are not evidence of a text edit.
8. **Aoi's verification hints for the superseded escrow**
   ([post](https://www.reddit.com/r/Grycoin/comments/cgkpbb/777_mbtc_quizchain_last_block/),
   [comment 4](https://www.reddit.com/r/Grycoin/comments/chn8un/comment/ev8a7gb/)): the
   funded key is the first in the list, its private key contains the digit 7 twice, and
   "the 7th private key in the list" contains 7 three times. Any candidate for the
   original hash gets these two free checks.

## Grycoin Block 2 (format example): tested, all negative

Base text: the archived question, whose LF LF MD5 is Aoi's published `7759227d…`. The
filter is her published `3c6` MD5 prefix, then the payout address at BIP44 indices 0–1
(0–19 for `flips20`).

| Family | Texts | `3c6` survivors | Result |
|---|---:|---:|---|
| `flips20`: every subset of toggles on all 20 paragraph first/last letters, LF LF and CRLF CRLF | 2,097,152 | 518 | 0 |
| The same 518 survivors on 9 other paths (`m/0`, `m/0'/0`, change chain, accounts 1–2, …), passphrase "" or "TOMI", compressed and uncompressed; SHA-256 as 24-word or truncated entropy | 518 | – | 0 |
| `drafts`: "Even after I explained…" removed or split off, every boundary-toggle subset, 4 joins | 20,971,520 | 5,117 | 0 |
| `trailingSpaces`: a trailing space after any subset of paragraphs, 5 sign sets, 3 flip modes | 61,440 | 9 | 0 |
| `sentenceEdits`: any non-first sentence or non-sign paragraph absent, then the sign rule | 4,320 | 0 | 0 |
| `sentenceLastLetter`: per paragraph, first letter plus the last letter of any one sentence (covers "himself"→"himselF") | 62,208 | 35 | 0 |
| `ffwwPlus2`: FFWW (5 flip modes) plus any 1–2 extra toggles anywhere | 7,170,030 | 1,699 | 0 |
| **FFWW plus any 1–3 toggles anywhere** (`md5-toggle-search.c`, LF LF and CRLF CRLF) | 571,692,786 | 139,381 | 0 |
| `missedBreaks`: any subset of the 9 joins single instead of double (or tripled), every boundary-toggle subset on paragraphs 2–7 | 6,279,168 | 1,519 | 0 |
| `insertDelete`: one deleted or inserted character (space, LF, CRLF, `.`, `"`, `'`) anywhere, every FFWW-flip subset | 5,586,944 | 1,387 | 0 |
| `doubleSpaces`: double space after any subset of sentences | 320 | 0 | 0 |
| Unusual joins (`\r\r`, `\n\r`, `\n \n`, `\n`NBSP`\n`, single space, `\n\n\n`, `\r\n\n`) × every subset of the 20 boundary toggles | 7,340,032 | 1,853 | 0 |
| The unmodified question (LF, CRLF, with trailing LF), the whole post, `[solution]`, the empty string: MD5 and SHA-256, indices 0–19 | 16 | – | 0 |

In all, 621,265,936 texts. Conclusion: the example's hashed bytes are **not** the posted question plus any small
case edit near the obvious answer under the tested derivation settings. A different
tool setting or serialization remains possible. Knowing puzzleponky's exact method
would help calibrate the Real Big Block.

## Real Big Block: tested this session, all negative

Both escrows. BIP44 indices **0–20**; the earlier public ledger derived only 0–5.

| Family (`chapter-variants.cjs`) | Texts |
|---|---:|
| `groupsWideIndex`: all 16 combinations of the 4 FFWW groups × 3 NBSP modes × 4 joins × 3 tails | 576 |
| `letterRules`: chapter-wide ITASM, SATOHIM and SATOHI rules; groups plus the preceding "I" paragraphs; heading 181 flipped or edited | 264 |
| `brPromote`: every subset of the 10 internal `<br>` promoted to full paragraph breaks | 12,276 |
| `stripped`: trailing spaces removed per paragraph, three NBSP normalisations | 144 |
| `truncated`: text cut at 23 common input-length limits | 156 |
| `twists`: quotation marks, repetition, brackets, title changes, reversed order | 180 |
| `otherPaths`: main families on 9 non-BIP44 paths, compressed and uncompressed | 64 |

In all, 13,660 distinct texts, 0 matches for either escrow.

## Leads, ranked

1. **Ask puzzleponky what differed in the example** (u/puzzleponky; last active 2020-06).
   One sentence ("the text differed by …") would calibrate Aoi's serialization. A 2026
   comment by u/Sea_Ferret_9615 asking the same thing has no reply yet.
2. **Aoi's Twitter, @NakamotoAoi.** She posted block questions and hints there ("A couple
   of hints at my Twitter feed @NakamotoAoi helped with the solution", block 20; the Grycoin
   Block 1 question was tweeted first). Nobody seems to have checked it for the example or
   Real Big Block. web.archive.org and archive.ph were unreachable from this environment,
   so try from an ordinary connection.
3. **Tablet edit artefacts on the Real Big Block.** The example shows her hashed bytes
   can differ from the published text in ways she could not explain herself. A GPU run of
   "groups flipped plus 1–2 arbitrary edits" on the chapter is about 2e9 texts per base per
   edit type. It is feasible with the existing `gpu-case-pairs.py` pipeline and fits this
   evidence better than blind pair toggles.

## Reproducing the three-toggle example search

```sh
cd followup-2026-09-25
node example-block-search.cjs --write-bases
gcc -O3 -march=native -pthread -o md5-toggle-search md5-toggle-search.c
./md5-toggle-search example-ffww-lf.bin example-letters-lf.txt 3 3c6 4 > lf.out     # ~2.5 min on 4 cores
node derive-survivors.cjs lf.out                                                     # ~70k survivors
# repeat with example-ffww-crlf.bin / example-letters-crlf.txt
```
