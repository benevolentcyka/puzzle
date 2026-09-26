# Grycoin Block 2: historical Coleman fixed-length modes

Completed CPU search: **zero matches** for the solved example address.

`node followup-2026-09-26/research/coleman-example-search.cjs` enumerates every subset of the 20 paragraph first/last ASCII letter capitalization toggles, with LF LF and CRLF CRLF joins, retaining all other archived question bytes and no trailing newline. It first verifies the author WIF vector, solved Stage One address and Grycoin Block 1 address. The unmodified LF question reproduces the published MD5 prefix `7759227` through the shared source loader.

Of 2,097,152 texts, 518 pass Aoi's published solution MD5 prefix `3c6`: 257 LF and 261 CRLF. Each survivor is tested as raw MD5 entropy and under ten historical fixed-length modes: SHA256 of the lowercase or uppercase ASCII MD5 hex string, truncated to 16, 20, 24, 28 or 32 bytes. BIP39 English, empty passphrase, compressed Bitcoin P2PKH, BIP44 account 0/external chain, indices 0–20 are used. Total: 5,698 entropy variants and 119,658 derived addresses, including 108,780 addresses for the ten added modes. Runtime was 140.631 seconds.

The mode is verified in the saved official [2019 Ian Coleman source](https://github.com/iancoleman/bip39/blob/45e40c288fe0d6cfba2c57a68f421eeb34d41385/src/js/index.js). This is SHA256 of **ASCII MD5 hex**, not chapter bytes or raw MD5 bytes. Historical HTML selects raw entropy by default, so this family needs a deliberate settings change. See `../verification/AUDIT.md` and `settings-vectors.json` for provenance.

`coleman-example-results.json` records counts, source/question hashes, and SHA256 of the ordered length-framed candidate byte stream plus survivor descriptor stream. Candidate text and keys are omitted from this report. No hit file was created. The negative is limited to these text mutations, prefix filter, modes and paths; it does not recover the actual example answer.
