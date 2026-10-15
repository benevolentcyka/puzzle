# Exact-sentence relocation test — 2026-10-15

**Complete, no match.** This is a bounded historical-draft test of the smaller
Grycoin Block 2 example, not a reconstruction of its successful claim buffer.

The archived [example post](https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/)
names the final `f` of `himself` as an endpoint, although the published paragraph
continues with `Even after I explained the method used and the result in detail.`
Previous code tested removing that exact sentence, making it a separate paragraph
in its current location, retaining every subset of the sentences in order, and
deleting/duplicating passages. Those operations do not in general move the same
sentence elsewhere while retaining all words.

This test moves only that exact sentence. Relocation is a hypothesis about a
possible earlier draft, not an author statement or an observed historical version.
It was selected because it specifically addresses the named-endpoint discrepancy.

## Finite bounds

- Remove the exact terminal sentence and its preceding ASCII space from original
  zero-based paragraph 4.
- Attach it before or after each of the ten remaining paragraphs, using one ASCII
  space. Exclude the original placement after paragraph 4: 19 placements.
- Alternatively insert it as a standalone paragraph at each of 11 positions.
- Apply six case rules: raw; paragraph initials F/W; paragraph initials absent
  from SATOSHI; explicitly named I/f; and each of the two selection rules combined
  with named I/f. Selected paragraph endpoints use first-lower/last-upper or both
  toggled. The named I is anchored to the original `I expected otherwise` sentence,
  even when it becomes interior to a paragraph.
- Use LF LF, CRLF CRLF, LF, or CRLF globally, without a terminal newline.
- Derive every distinct buffer with no prefix filter: raw MD5, English BIP39,
  empty passphrase, compressed P2PKH at `m/44'/0'/0'/0/i`, indices 0–6.
- Compare the example target and both final-block targets.

The 30 placements × 6 rules × 2 case modes × 4 joins generated 1,440 operations,
with 1,056 distinct exact text buffers. The loop order, all exact placements,
source hashes, runner hash, and serialization rules are recorded in `plan.json`
and repeated in `results.json`. This family overlaps previous tests; its size is
not a count of candidates new to the entire investigation.

## Verification and result

The unmodified source reproduced all 1,549 bytes and full MD5
`7759227d7406d8230d7e3a8f7b9846d7`. Stage One, Grycoin Block 1, and the author's
published converter vector passed. An invariant checks that each case rule
preserves every non-case character. Every candidate's seven addresses agreed
between `followup-2026-09-25/lib.cjs` and `verifier.cjs`.

| Measurement | Result |
| --- | ---: |
| Distinct exact candidate buffers | 1,056 |
| Primary address derivation operations | 7,392 |
| Independent address comparisons | 7,392 |
| Public target comparisons | 22,176 |
| Buffers matching the optional 3c6 hint | 1 |
| Verified target matches | 0 |

Length-prefixed candidate stream SHA256:
`810f2e304112d1ef5e0e3cb522f28e4be49c81dd2a3c84965fb305b13b6f335e`.

No recovered solution, mnemonic, or private key is in this report. Successful
material, if a future invocation finds any, is saved only in local `FOUND-*`
files; `.gitignore` excludes those names. The original investigation repository
was not modified by this test.

This excludes only the stated relocation/case/serialization/derivation family.
It does not exclude arbitrary sentence order, another capitalization mask,
additional byte edits, another converter setting, or another index.

## Reproduce

```powershell
node .\search.cjs --repo 'C:\Users\boomb\Downloads\puzzle-investigation' --output .
```

The runner defaults to that repository path and its own directory as output.
It makes no network requests and does not sign or broadcast transactions.

An earlier unsaved exploratory run used a flawed named-I relocation model and
reported 1,048 buffers. It is superseded by the corrected, recorded 1,056-buffer
run above; only the latter has a complete manifest and independent comparison.
