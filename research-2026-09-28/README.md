# Source research, 2026-09-28

## Wattpad story parts

`wattpad-parts/manifest.json` lists all 33 parts of story 184148284 ("Second",
description **"Hint for block 77."**, tag `hintforblock77`). Each part was
fetched read-only from the public `apiv2 storytext` endpoint and gzip-decoded,
then recorded with its size and SHA-256. The full texts are kept locally
(`*.html` is git-ignored) rather than redistributed. The chapter response
(720888559) is byte-identical to the saved `wattpad-api-720888559.txt` after
LF normalisation.

Observations used by `../calibrated-2026-09-28/`:

- **"Second Life" (720889517, April 2019)** contains the same 17 lines as the
  block 29 draft. Each single-LF draft line became its own `<p>`, and the first
  has a stray leading `<br>`.
- **"THOMAS and SATOSHI" (757574334, 2019-07-17)** is an earlier copy of
  chapter §III.2.b. It already has the `<br>` sites later seen at chapter
  paragraphs 188 and 192, plus a mid-sentence `where the <br>name` that the
  chapter no longer has. Chapter paragraph 183 appears here as **two separate
  paragraphs**, so the chapter's `<br>` joined them. Here `anagram. What` has
  one space; the chapter has `NBSP+space`. The chapter text was therefore
  re-edited when assembled on 2019-07-22/23.
- **"Mistakes" (724275249)** says the author hashes on a tablet whose hashing
  tool defaults to MD5. It lists copy-pasted line breaks and extra spaces as
  her past hashing errors.
- **"Starting Up" (762380140, modified 2019-07-23T23:24Z)** says that after
  the restart she had "lost any information on the solution". The chapter's
  own modifyDate is 12 minutes earlier (23:12Z). Moving the escrow on
  2019-07-30 shows she could sign with the old key. It does not show she still
  had the exact source text. This is why a *copy of the published chapter* is
  kept as an alternative base to her draft.
- **"The Satoshi Code" (761570746)** concerns the first-run genesis-address
  block 77 (MD5 hint prefixes `cc9485a`, `d78c92f`), not the chapter buffer.
- Story metadata `length: 45451` equals the LF LF-joined parsed chapter
  (45,450 characters) plus one. It is consistent with the stored content and
  gives no evidence of a content change.

## Archive lookup

`cdx-chapter.json`: the Wayback CDX query for the URL prefix
`wattpad.com/720888559*` succeeded on retry and returned **zero captures**.
The story-page queries failed (HTTP 503/504) and prove nothing. There is
therefore no archived July 2019 copy of the chapter page to diff against the
current text.

## Author statements that constrain the revised answer

| Date (UTC) | Source | Statement |
| --- | --- | --- |
| 07-25 | `euvdqxe` | Extra line breaks were added when posting to Wattpad; "This information is needed to solve the block." |
| 07-28 | `ev96vwg` | The (original) solution "has only one line break between paragraphs". |
| 07-30 | post `cgkpbb` update | Prize moved "because I wanted to remove **one of the twists I had**… It is **also** hashed with two line breaks between paragraphs now." |
| 07-31 | `evj8ls1` | "It has multiple paragraphs and two line breaks between each of them." |
| 08-01 | `evn5g4u` | "Hit enter twice." |
| 08-03 | `evwv4rm` | For the example, "how to go from that to claiming the prize is not [obvious], not even to me." |
| 08-03 | `evwviwy` | For Stage One, she does not know the solver's "tricky bits". |

The last two, together with the verified Stage One buffer (it includes
`[edited slightly]`), show that the author's hashed buffers contain artifacts
she was unaware of.
