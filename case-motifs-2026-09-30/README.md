# Intraword capitalization and nearby initials, 2026-09-30

**UNSOLVED.** The source contains unusual `ppM`, `VIrgin`,
`BItcoin`, and explicit `BITcoin`/`AHScoin` labels. These supply
seven uppercase letters inside words at paragraphs 72,127,135,208.
The author demonstrated an internal `vOIce` change in solved Block 29.
These observable letters motivate a small case family without presuming
they are errors or instructions to normalize the entire chapter.

## Actual scope and results

1. Independently toggle the seven capitals, plus either/both known
   `vOIce` pairs (paragraphs 11/23), plus the whole `SECOND` title
   motif when the title is included. 524,288 instances across 768 bases;
   indices 0–6 = **3,670,016** addresses. **Complete, no match.**
2. `--mixed-only --near-initials`: independently choose all seven capitals
   AND the eight nearby initials, preserving each coherent FFWW baseline.
   2¹⁵ masks × 768 bases = **25,165,824** candidates at index 0.
   Current checkpoint: **25,165,824**, complete=true,
   matches=0. The voice/title motifs are omitted in this run.

The union of a capitals-only negative and an initials-only negative does not
exclude their combinations; run 2 checks that gap. Every bit-mask group is
mapped back to original character locations and compared with an independent
rebuild. GPU MD5 is certified per base, every wallet batch is checked on CPU,
and solved Stage One/Grycoin Block 1 pass on startup. No prefix filter is used.

```powershell
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\case-motifs-2026-09-30\search.py --mixed-only --near-initials --indices 0
```

Same arguments resume the configuration-fingerprinted checkpoint. Different
index lists or inclusion of the voice/title motifs define different runs;
they are not automatically covered by the result above.
