# Independently selected paragraph cases, 2026-09-30

**UNSOLVED.** The chapter writes `I STNM`, while its marked paragraphs
supply F,F,W,W initials and S,T,N,M endings. Earlier structured-twist searches
coupled the first and last letters of any added nearby paragraph
(`calibrated-2026-09-28/twist-search.py:pattern_ops`). That does not cover
all independent choices of their ends. Arbitrary endpoint triples also do not
cover four or more changes outside the 32 marked endpoints.

## Completed

- **Nearby initials:** independently toggle the first letter of paragraphs
  3,8,9,91,164,165,166,233, on all 768 source-format bases. 196,608 candidate
  instances × indices 0–6 = **1,376,256** addresses, no match. Includes the
  plausible preceding `I` letters together and all subsets.
- **Every marked paragraph pair:** independently include/omit first+last
  changes for EACH of the 16 FFWW paragraphs. This is broader than choosing
  coherent whole groups. 65,536 masks × 48 formats = **3,145,728** candidates,
  **22,020,096** addresses, indices 0–6, no match.
  Some masks were covered by the prior radius-10 family; others were outside it.

Both are unfiltered, English/raw MD5/empty passphrase, compressed BIP44.
The rank-to-mask mapping for the second run was checked independently for all
65,536 masks. Source rebuilds, GPU MD5 and CPU wallet comparisons are recorded
in the checkpoints. Positive controls pass at startup.

## Broader next local run: first AND last independently

`search.py --endpoints both` selects both ends of the same eight nearby
paragraphs independently (16 bits), while preserving the coherent FFWW-group
selection in each of 768 bases. All 2¹⁶ masks are allowed, not a radius cutoff.
No spelling changes or voice/title motifs are added.

The benchmark checked **278,528 / 50,331,648**
candidate/address operations at index 0, zero matches, **PARTIAL**.
**50,053,120 remain.** It took 11.1s,
about 25,034/s while other
GPU runs shared the device. Plan **20–40 minutes** on this machine; use the
live estimate. This is a tested, bounded hypothesis, not a guaranteed solution.

```powershell
Set-Location 'C:\Users\boomb\Downloads\puzzle-investigation'
& 'C:\Users\boomb\AppData\Local\Programs\Python\Python312\python.exe' .\near-case-2026-09-30\search.py --endpoints both --indices 0 --platform 1
```

A separate invocation demonstrably resumed from 262,144 to 278,528, checking
16,384 further candidates in about 0.5s. It loaded the existing fingerprint
and saved additional progress successfully.

This resumes `near-both-6555be4d17950571.json`. `--limit N` limits
additional candidates; omit it for completion. Ctrl+C may repeat an unsaved
batch. Code/source/kernel fingerprints, atomic JSON saves and an OS lock
protect resume identity. A full address match must pass CPU reconstruction
and derivation before exact bytes and keys are saved locally.

The script-policy problem is avoided by invoking Python directly.
This run includes many overlaps with prior endpoint sweeps and the completed
initials run; counts are operations, not unique wallets.
