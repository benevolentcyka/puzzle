# Cracking the solved example (Grycoin Block 2)

**Goal, not yet achieved.** The example prize `1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi`
(700,000 sats, funding `f11eca99…`) was **claimed in 2019**, so an exact answer
buffer exists. The author said knowing the example helps the final block, but
that she does **not** know how the solver went from the capitalization to the
claim ([`evwv4rm`](https://www.reddit.com/r/Grycoin/comments/cleczc/comment/evwv4rm/)).
Her published intended-answer hint was prefix `3c6`; the earlier large case-mask
sweeps derived **only `3c6`-prefix survivors** into wallets, so any claim buffer
whose MD5 does not start with `3c6` (e.g. the solver used a quirk she didn't
intend) was never tested against the real address.

This searches **every** candidate (no prefix filter) against the actual
address. The example question is 10 paragraphs / 1,197 ASCII letters, LF LF
joins (the form that reproduces the author's published `7759227` prefix).

## Baselines (sign paragraphs get first ASCII letter lowered, last raised)

| Name | Sign paragraphs | MD5 |
| --- | --- | --- |
| `raw` | none | `7759227d…` (author's published prefix `7759227`) |
| `ffww-quad` | 2,3,6,7 (the F,F,W,W quad) | `31bf6e23…` (= handoff's "obvious FFWW") |
| `non-itasm` | 2,3,5,6,7 (every non-I/T/A/S/M start) | `36f6f7bf…` |
| `author` | ffww-quad **plus** her described `I`→`i` (¶4) and `himself`→`himselF` | `a3bbc2d7…` |

From each baseline the tool applies every combination of up to `--max-toggles`
ASCII case flips over all 1,197 letters, MD5s, derives English BIP39 / empty
passphrase / `m/44'/0'/0'/0/i`, and compares the example address plus (free)
both final prize addresses. Startup runs the Stage One + Block 1 controls; every
batch is CPU re-derived and re-serialized. Hits go only to git-ignored `FOUND-*`.

## Results

| Baseline | Toggles | Candidates | Index | Result |
| --- | ---: | ---: | :--: | --- |
| raw | ≤2 | 717,004 | 0 | no match |
| ffww-quad | ≤2 | 717,004 | 0 | no match |
| non-itasm | ≤2 | 717,004 | 0 | no match |
| author | ≤2 | 717,004 | 0 | no match |
| ffww-quad | ≤3 | 285,846,394 | 0 | running |

So the example claim buffer is **not within two case-flips** of any plausible
baseline at index 0. If the ≤3 passes are also negative, the claim buffer is
more than three case changes from the obvious readings — pointing at a
formatting/edit quirk (already heavily searched: see `followup-2026-09-26`,
`assumptions-2026-09-27`) or a derivation the historical matrix did not cover,
rather than a simple deeper case pattern.

```powershell
& $py .\example-crack-2026-09-29\search.py --baseline ffww-quad --max-toggles 3 --indices 0 --platform 1
```

Resumable from `example-<baseline>-t<toggles>-i<indices>.json`.
