# Block 29: a reproduced long-text positive control

**Result: reproduced.** Quizchain round-1 block 29 is the closest solved analog
of the final block: an early draft of the *same chapter* (paragraphs 10–27 of
"Second"), hashed by the same author from her draft, with a disclosed
capitalization answer. It had never been reconstructed in this repository.

## Primary sources

- [Block 29 post](https://www.reddit.com/r/bitcoinpuzzles/comments/bc6rkn/easy_7_mbtc_quizchain_block_29/),
  archived selftext in `aoi-posts-archive.json` (id `bc6rkn`). The author's
  update says: *"Copypaste from my draft, exactly same as used for hashing"*,
  followed by 17 lines. The extracted text has exactly **235 words**, matching
  her later remark that the solution had 235 words.
- Solution (same post, and the round-1 solutions list in part 720895205):
  change `o` and `i` in `voice` in the second sentence to `O` and `I`.
- Format: `[solution] [link]` with one space; the link is the last three
  characters of the (unpublished) block 28 private key.
- Funding transaction `b49ebc67d4fc54143b0a934441224f6abeb4749d24f7e14776294dfdfeaa7d77`
  output 0: `1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P`, 770,000 sats. This matches
  her remark "It was actually 7.7 mbtc this time". Retrieved read-only from
  mempool.space on 2026-09-28. The prize was claimed in 2019.
- Round-1 block 30's disclosed answer ends in link `JRu`, which must be the
  last three characters of the block 29 private key.

## Search and result

`search.py` enumerates all 58³ Base58 links × {LF, CRLF} line endings ×
{MD5, SHA-256} entropy: 780,448 candidates, English BIP39, empty passphrase,
`m/44'/0'/0'/0/0`. It uses the repository's verified GPU wallet path. At
startup it runs the Stage One and Grycoin Block 1 positive controls, then CPU
spot-checks every batch.

| Field | Value |
| --- | --- |
| Line endings | **LF** (`0a`), one draft line per paragraph |
| Hash | **MD5** of raw UTF-8, no trailing newline |
| Link | `zff` |
| Entropy | `982301b80b30af3a0abe110269b0dd43` |
| Hashed length | 1,360 bytes |
| Derived address | `1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P` |
| Derived WIF suffix | **`JRu`**: independently equals block 30's published link |

The `JRu` agreement is a second, independent confirmation: it comes from the
private key, not from the address comparison. `block29-result.json` stores
the non-secret facts. The historical WIF and mnemonic are only in git-ignored
`FOUND-block29.json`.

```powershell
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\control-block29-2026-09-28\search.py --platform 1
```

It found the match after about 180,000 candidates (under 10 seconds).

## What this establishes

1. The author's **draft → hash** path for multi-paragraph chapter text is the
   exact draft bytes with **LF**, MD5, and nothing before or after. This is the
   third independent LF calibration, after Stage One (a web copy) and the
   example's raw-question prefix `7759227`. Her own "13 10" descriptions came
   from asciivalue.com, a form-based tool, and are not what her hashing tool received.
2. The draft stores **one paragraph per line** (single LF). This agrees with her
   pre-migration statement that the original final solution had "only one
   line break between paragraphs".
3. A posted "exactly same as used for hashing" copy was byte-exact apart from
   the stated case change.
4. The author's capitalization twists can sit *inside* a sentence (`vOIce`),
   not only at paragraph endpoints. The sentence "A pleasant female voice."
   survives unchanged as paragraph 11 of the final chapter.

It does **not** establish the final answer's case pattern or prove that the
final was hashed from a draft rather than a copy of the published chapter.
