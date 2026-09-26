# Text evidence audit, 2026-09-26

Status: unsolved. This pass found no new secret, winning hash, or historical answer copy. It refreshed three primary Wattpad responses and narrowed what their structure actually proves. Indices below are zero-based.

## Fresh primary evidence

Retrieved with Node fetch on 2026-09-26:

- https://www.wattpad.com/apiv2/?m=storytext&id=720888559 -> live-720888559.html; SHA256 abf15822b6785ae79eaf7c00b401b2730891c03646b40aae985eb3bc31126bbc (59,613 response bytes).
- https://www.wattpad.com/apiv2/?m=storytext&id=724275249 -> live-724275249.html; SHA256 b3baa88138264c1a73517eed1c6d45c17a0cbaa21023b2b5818efc4f26370910 (3,508 response bytes).
- https://www.wattpad.com/apiv2/?m=storytext&id=762380140 -> live-762380140.html; SHA256 8ce38fbe29d9844569715ebdaff3087982a1fde7af6dce19851d95f5c2d89db8 (2,561 response bytes).
- https://www.wattpad.com/api/v3/stories/184148284?fields=parts(id,title,modifyDate,publishDate) -> all-part-meta.json. The API returned modifyDate but omitted requested publishDate. Second: 2019-07-23T23:12:04Z; Mistakes: 2019-04-28T00:52:59Z; Starting Up: 2019-07-23T23:24:07Z.

After normalizing storage CRLF to LF, the refreshed Second response equals the existing saved API response. This establishes stability between these two captures, not stability since 2019. modifyDate is metadata evidence, not an independent historical snapshot.

byte-audit.json confirms 273 paragraphs, 10 internal br tags, and 6 NBSP characters. The ten internal breaks are at paragraphs 62, 72, 120, 123, 145, 159, 183, 188, 192, 212. Exactly 13 paragraphs end in an ordinary space: 85, 107, 121, 127, 138, 146, 164, 165, 191, 200, 208, 219, 266. No global trim should be silently applied.

The stored body itself begins with a paragraph containing Second, separately from the part title in metadata. Thus including Second once is a body-text extraction; including it twice is a page-title-plus-body extraction. This ambiguity is already covered by the public title/header tests and is not a new search family.

Every paragraph except the duplicate occurrence at 77 matches its data-p-id MD5 when tags (including br) are removed and HTML entities decoded. Importantly, those paragraph IDs do not encode the br characters, so their agreement cannot certify whether the copied plaintext contained LF, CRLF, a space, or nothing at those internal breaks. The duplicate behavior was previously calibrated on part 720895205; nothing here undermines that explanation.

## Constraints and cautions

Mistakes establishes tablet use and states that extra spaces or line breaks had previously caused errors in blocks 9 and 10. It does not establish which device, browser, hash tool, or line-ending normalization was used for the final block. The LF hypothesis is supported directly by the reproduced Grycoin example hash; tablet use is only a possible explanation.

Starting Up says the author lost information on the solution. Spending the old escrow later establishes access to a usable signing key, not retention of the exact source text. It is therefore stronger than the evidence to label the lost-information statement false or persona merely from that spend. A stored WIF can survive independently of the text used to derive it.

The chapter's ITASM selector sentence concerns the quoted Finney post explicitly: it refers to paragraphs of this post and then quotes the four exceptions. Applying ITASM to all 273 Wattpad paragraphs is an extrapolation, already tested negatively. The three narrative FFWW groups are a stronger local analogue; the fourth FFWW group is a quotation of Stage One. Existing exhaustive 17-paragraph subset work covers their simple combinations. There is no justification to present all-chapter ITASM as confirmed final-stage selection.

## Completed bounded family not clearly enumerated in the reviewed ledgers

Mixed internal-br deletion: independently retain or delete each of the 10 internal newline positions, preserving every neighboring ordinary space. Combine with no planted-group flips, three narrative groups, or all four groups; LF-LF versus CRLF-CRLF paragraph joins; NBSP retained versus ordinary-space substitution. This is at most 1024 x 3 x 2 x 2 = 12,288 candidate strings before deduplication, with current and superseded addresses at BIP44 index 0 as the primary check.

Rationale (hypothesis): some internal breaks separate sentences/dialogue and others split a line mid-sentence. The saved paragraph IDs are compatible with removing all tags, while visible browser text retains internal line breaks. A mixed copy/edit artifact could retain some and remove others. The public ledger enumerates br promotion, section splits, and broad copy serializations, but does not explicitly enumerate every subset of internal-br deletion. The September 25 brPromote family explicitly replaces internal LF with a full paragraph separator; that is a different operation from deletion. Executed with br-deletion-search.cjs: all 12,288 generated strings had distinct MD5 digests; 86,016 addresses at indices 0 through 6 were checked against both escrows (172,032 comparisons), with zero matches. The deterministic length-prefixed UTF8 candidate stream SHA256 is 060a1279fecb7883636908c3e1e2aced11fd7d704f1151b00a6568e300847007. Existing Stage One and Grycoin Block 1 derivation selftests passed, as did all paragraph-count, NBSP-count, retained-break, and canonical-line-ending assertions. See br-deletion-results.json for counts and source digest. This bounds precisely this family; it may overlap undocumented candidates in larger historical runs.

An exact 2019 answer buffer would still be much more valuable than another weakly motivated search family. No available metadata or paragraph-ID check establishes that buffer.
