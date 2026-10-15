# Quizchain investigation — 2026-10-15

**UNSOLVED. No final answer, matching key, or reconstructed Grycoin Block 2
claim buffer was recovered.** Two new, finite hypotheses were tested to
completion, with no matches. The work was offline except for reading the public
announcement, discussion, and example on Reddit. No person was contacted and
no transaction was signed or broadcast.

## What was actually established

The actual 273 saved paragraphs, author audit, primary posts, exhausted inventory,
September 30 results, completion observation, and relevant enumeration code were
read before selecting tests. The two new families follow specific textual clues;
they do not broaden an arbitrary capitalization radius.

Reproduced controls:

- Stage One from the saved Finney HTML: MD5
  `9dd2efb9bc976c2095bd534d7b8d431c`, address
  `19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN`.
- Grycoin Block 1 from `Still 21st Century`: address
  `18EpYz5qB3XoxZWouJF3KdEp3E2nfv9FgP`.
- The author's public converter vector passed `node verifier.cjs --selftest`.
- Block 29 reconstructed from the archived draft, changing `voice` to `vOIce`
  and appending the previously recovered public link `zff`: 1,360 bytes, MD5
  `982301b80b30af3a0abe110269b0dd43`, address
  `1BQiU45feRw5UKdCUbXuoNfuK5WRzTpa4P`, WIF suffix `JRu`.
- The unmodified smaller example reproduced 1,549 bytes and MD5
  `7759227d7406d8230d7e3a8f7b9846d7`.

These establish the known controls. They do not establish the final answer's
serialization or derivation settings. OpenCL platform 1 was confirmed as the
NVIDIA GeForce RTX 4060 Laptop GPU on this machine.

## Global endpoint signs

Paragraphs 228–235 connect FFWW initials to STNM endings; paragraph 240 assigns
meaning to both sets. The [later format example](https://www.reddit.com/r/Grycoin/comments/cleczc/grycoin_block_2/)
says to change the relevant letters in all paragraphs where the signs are
recognized. A concrete extension is to recognize each ordered endpoint pair
throughout the chapter rather than require membership in a contiguous quartet.
This extension is a hypothesis, not an explicit instruction from the author.

Zero-based paragraph indices, using first and last ASCII letters:

| Pair | Matching paragraphs |
| --- | --- |
| F…s | 4, 92, 99, 167, 230 |
| F…t | 5, 93, 168, 231 |
| W…n | 6, 51, 94, 138, 151, 156, 169, 232, 264 |
| W…m | 7, 29, 95, 170, 234 |

The union adds **29, 51, 99, 138, 151, 156, 264** to the original sixteen.
Excluding headings 151/156/264 leaves four extra paragraph pairs. The full and
heading-excluded unions are outside the previous two-extra-paragraph family.
Prior marked-endpoint and nearby-I families also do not cover these extra sites.
Other candidates in this test overlap earlier searches; no global novelty count
is claimed.

`endpoint-signs/search.py` enumerates all 16 pair-type subsets, headings
included/excluded, quoted Finney passage 230–234 included/excluded, first ASCII
letter versus literal first character, and three case modes (both endpoints,
first only, last only). Literal-first excludes a leading quote or heading digit;
it is a separate interpretation, not a change to the source text.

Each selection uses eight established byte layouts, starts at paragraph 0/1/3,
and no terminal newline or one LF. The layouts are draft/rendered/promoted/app
LF-LF, draft/app single LF, CRLF-CRLF with internal LF, and fully normalized
CRLF. See `endpoint-signs/plan.json` for all exact policies and source hashes.

| Measurement | Completed result |
| --- | ---: |
| Enumeration operations | 18,432 |
| Distinct buffers by SHA256, also distinct MD5 values | 10,272 |
| Address derivations, indices 0–6 | 71,904 |
| Comparisons to both final targets | 143,808 |
| Independent CPU address comparisons | 65, including two GPU positive controls |
| Verified matches | 0 |

No MD5-prefix filter was used. Each buffer used raw MD5 entropy, English BIP39,
empty passphrase, and compressed P2PKH at `m/44'/0'/0'/0/i`. An independent
review reconstructed 48 serializer/start/tail cases byte-for-byte, checked the
exact paragraph manifest, and reviewed match-row indexing. Existing GPU support
compared sampled mnemonic, seed, key, public key, and hash160 against CPU results.

The length-prefixed exact candidate-stream SHA256 is
`0a00772f5b3da8831faf8fc7a938eaa340dd296b3f716af6ab778fdaedc9c4b9`.
The complete receipt is `endpoint-signs/results.json`. No earlier checkpoint
was reused. This negative excludes only the enumerated family at these settings.

## Smaller example: relocate its contradictory sentence

The author identifies `himself` as an ending, but the saved paragraph continues
with `Even after I explained the method used and the result in detail.` Earlier
tests removed or split that sentence. The new test moves that exact sentence,
retaining all words, to each paragraph boundary or before/after another paragraph.
This tests a possible historical draft; no such draft was recovered.

Thirty placements, six case rules, two case modes, and four newline policies
generated 1,440 operations and **1,056 distinct exact buffers**. All **7,392
addresses** at indices 0–6 agreed between two CPU implementations. None matched
the example or either final target. One buffer met the `3c6` prefix, but every
buffer was derived regardless of that hint. See
`example-relocation/README.md`, `plan.json`, and `results.json` for exact bounds.

## Evidence corrections and remaining uncertainty

1. The September 30 remaining-I-signature family is **user-confirmed complete**,
   not a new continuation. The local `completion-observation.json` records
   29,393,280 candidates and 205,752,960 address operations, with zero matches,
   plus explicit user confirmation. The current runner checkpoint reverted to
   its 65,536-candidate pilot. This is recorded observation/testimony, not a
   surviving byte-exact completed receipt; this investigation did not alter or
   reconstruct it and did not rerun that family.
2. In paragraph 237, the described sentence identifies **paragraph 233** as the
   nearby I. Applying the idea to other nearby I initials is an analogy.
3. A historical claim establishes access to a spending key; it does **not**
   demonstrate that the published example's intended case transformation
   generated that key. The [author's reply](https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evwv4rm/)
   says she did not know the successful claiming method. The raw-question hash
   prefix is a valid byte control, while the example's answer-to-target mapping
   remains unreconstructed. This observation does not prove either puzzle
   impossible or the advertised derivation wrong.
4. The [revision announcement](https://www.reddit.com/r/Grycoin/comments/cgkpbb/777_mbtc_quizchain_last_block/)
   and [discussion](https://www.reddit.com/r/Grycoin/comments/chn8un/real_big_block_discussion/)
   support the two-break instruction. The historical LF controls do not settle
   every byte in the final chapter. No July 2019 answer buffer was obtained.

The strongest unresolved issue is still the exact historical hashing input and
the smaller example's unreconstructed mapping. A larger search is not justified
merely by these negative results. Any further test should specify a new clue,
source discrepancy, or implementation defect first.

## Reproduce from the repository root

```powershell
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\quizchain-2026-10-15\endpoint-signs\search.py --repo . --platform 1
node .\quizchain-2026-10-15\example-relocation\search.cjs --repo .
```

The original uncommitted research files were preserved. This directory contains
only new code, manifests, results, and notes. Newly recovered answer material
would remain in ignored local `FOUND-*` files pending separate authorization.
