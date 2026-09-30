# Single ASCII copying/editing faults, 2026-09-30

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

`search.py`/`single-edit.cl` are the initial byte-by-byte implementation.
It passed 5,733 independent MD5/enumeration fixtures. Its all-operation pilot
reached **10,390,886** before replacement by the faster implementation;
the old checkpoint remains partial and is superseded, not added as coverage.

`search-fast.py`/`fast-edit.cl` use word-based reconstruction and
vectorized enumeration. They passed **7,781** independent checks, including
changed MD5 padding boundaries, arbitrary binary short fixtures, independent
edit ordering, and 2,048 full-chapter edit checks. Every search batch samples
first/middle/last MD5s against `hashlib`, and independently checks BIP39,
PBKDF2, BIP32, public keys and full hash160 on CPU. Stage One and Grycoin
Block 1 are actual matching positive controls. Matches stay in ignored
local `FOUND-*` files after CPU confirmation.

The faster run restarted at rank 0 under a new code/kernel fingerprint;
no checkpoint was renamed or transferred. The authoritative checkpoint is
`one-edit-all-calibrated-fb17a2b64e5cca12.json`. Its recorded search time is
**1560.5s**, on this RTX 4060, including periods
with another GPU job sharing the device.

## Reproduce

```powershell
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\single-edit-2026-09-30\search-fast.py --family all --indices 0
```

This complete checkpoint skips the search. A different index list defines a
different run. Deletion/duplication indices 0–6 are already complete; do not
repeat them to claim new work. Do not run Python with `-O`.
