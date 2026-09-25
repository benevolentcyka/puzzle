# AoiNakamoto public account audit (2026-09-26)

I fetched the historical public-account listings from Arctic Shift, sorted
newest-first and paginated to exhaustion. The saved files contain 202 posts
(`aoi-posts-archive.json`) and 864 comments (`aoi-comments-archive.json`),
dated 2019-04-02 through 2019-08-04. They cover the account history returned
by that archive, including 87 posts in r/Grycoin and 90 in r/bitcoinpuzzles,
and 316 and 432 comments in those communities, respectively. Deleted,
unarchived, or subsequently edited material cannot be ruled out. API:

`https://arctic-shift.photon-reddit.com/api/posts/search?author=AoiNakamoto&limit=100&sort=desc`

`https://arctic-shift.photon-reddit.com/api/comments/search?author=AoiNakamoto&limit=100&sort=desc`

The primary puzzle-relevant findings from the account history are:

| Date | Aoi source | Implication |
| --- | --- | --- |
| 2019-04-11 | [Quizchain Block 29](https://www.reddit.com/r/bitcoinpuzzles/comments/bc6rkn/easy_7_mbtc_quizchain_block_29/) | A previous long-text answer changed only `o` and `i` inside `voice` to `O` and `I`; the rest of the text was retained. That block also required a link suffix, an extra condition absent from the revised final block. |
| 2019-07-22/30 | [777 mBTC final block](https://www.reddit.com/r/Grycoin/comments/cgkpbb/777_mbtc_quizchain_last_block/) | The question was the final version of Wattpad chapter 2. On July 30 Aoi moved the prize to a new funding transaction, removed one twist, and said it was then hashed with two line breaks between paragraphs. |
| 2019-07-28 | [Discussion comment](https://www.reddit.com/r/Grycoin/comments/chn8un/comment/ev96vwg/) | Before the revision, Aoi described one CRLF between paragraphs, while the published chapter displayed two. The later revision supersedes this statement. |
| 2019-07-30 | [Discussion comment](https://www.reddit.com/r/Grycoin/comments/chn8un/comment/eve843h/) | Solving Stage One's format would hint at Stage Two's format. |
| 2019-07-31 | [Discussion comment](https://www.reddit.com/r/Grycoin/comments/chn8un/comment/evj8ls1/) | Aoi confirms the revised solution has multiple paragraphs and two line breaks between them. |
| 2019-08-03 | [Grycoin Block 2](https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/) | Aoi says both stages of block 77 use a long text kept intact except for capitalization of selected letters. She specifically directs solvers to retain the remaining text unchanged. |
| 2019-08-03 | [Format example comment](https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evv9k37/) | The published unmodified-question MD5 begins `7759227`. The archived question, joined with LF LF, reproduces the **full** MD5 `7759227d7406d8230d7e3a8f7b9846d7`; CRLF CRLF yields `e997007971f6f17c8775d83f30edb4c6`. Aoi's verbal CRLF description therefore does not reliably identify the actual bytes of this example. This does not prove the final chapter used LF LF. |
| 2019-08-03 | [Aoi's solver reply](https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evwv4rm/) | After the example was claimed, Aoi said she knew which capitalization to change but did not know how the solver went from that to the prize. This is direct evidence of an unresolved derivation/serialization twist, not evidence that the final block is impossible. |

I searched all saved text for puzzle names, capitalization, paragraph and
line-break language, the target chapter, and related solved blocks. The
relevant comments above are the strongest constraints on Stage Two. No
published full final answer, final MD5 digest, or private key appeared in
the returned archive.

`mini-format-test.py` independently tests the later example's exact archived
question under both LF LF and CRLF CRLF, zero to two arbitrary ASCII
capitalization toggles, its published `3c6` MD5 prefix, and BIP44 indices
0-6. None reproduces that example's payout address; see
`mini-format-results.json`. This is a deliberately bounded test.

In the separate Wattpad [Starting Up](https://www.wattpad.com/762380140-starting-up)
part (saved as `wattpad-api-762380140.txt`), Aoi says she lost information on
the real big block's solution after shutting down and restarting. That is
an author statement about her records, not proof that the key cannot be
reconstructed from the puzzle.
