'use strict';
// Independent subsets of internal <br> deletion, preserving adjacent spaces.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('assert/strict');
const L = require('../../followup-2026-09-25/lib.cjs');
L.selftest();
const paras = L.chapterParagraphs();
assert.equal(paras.length, 273);
assert.equal(paras.join('').split('\n').length - 1, 10);
assert.equal(paras.join('').split('\u00a0').length - 1, 6);
assert(!paras.join('').includes('\r'));
const groups = {
  raw: [],
  three: [...L.GROUPS.g1, ...L.GROUPS.g2, ...L.GROUPS.g3],
  four: Object.values(L.GROUPS).flat(),
};
const popcount = n => { let c = 0; while (n) { c += n & 1; n >>>= 1; } return c; };
const stream = crypto.createHash('sha256');
const seen = new Set();
const matches = [];
const perFamily = {};
let generated = 0, tested = 0, checks = 0;
const started = new Date().toISOString();
for (const [group, selected] of Object.entries(groups)) {
  const set = new Set(selected);
  const base = paras.map((p, i) => set.has(i) ? L.flip(p) : p);
  for (const sep of ['\n\n', '\r\n\r\n']) for (const nbsp of ['keep', 'space']) {
    const family = `${group}/${sep === '\n\n' ? 'LF' : 'CRLF'}/${nbsp}`;
    perFamily[family] = {generated: 0, uniqueTested: 0};
    for (let mask = 0; mask < 1024; mask++) {
      let br = 0;
      const pieces = base.map(p => {
        let q = p.replace(/\n/g, () => (mask & (1 << br++)) ? '' : '\n');
        if (nbsp === 'space') q = q.replace(/\u00a0/g, ' ');
        return q;
      });
      assert.equal(br, 10);
      assert.equal(pieces.join('').split('\n').length - 1, 10 - popcount(mask));
      const canonical = pieces.map(p => sep.startsWith('\r') ? p.replace(/\n/g, '\r\n') : p).join(sep);
      assert(!canonical.includes('\r\r\n'));
      assert.equal((canonical.match(/\n/g) || []).length, 544 + 10 - popcount(mask));
      if (sep.startsWith('\r')) assert.equal(canonical.replace(/\r\n/g, '').includes('\r'), false);
      else assert.equal(canonical.includes('\r'), false);
      // Length-prefixed UTF8 records; deterministic group/join/NBSP/mask loop order.
      const bytes = Buffer.from(canonical, 'utf8');
      const length = Buffer.alloc(4); length.writeUInt32BE(bytes.length);
      stream.update(length).update(bytes);
      generated++; perFamily[family].generated++;
      const digest = L.md5(bytes);
      const identity = digest.toString('hex');
      if (seen.has(identity)) continue;
      seen.add(identity); tested++; perFamily[family].uniqueTested++;
      const addresses = L.bip44Addresses(digest, 7);
      checks += addresses.length;
      addresses.forEach((address, index) => {
        if (address !== L.PRIZE && address !== L.SUPERSEDED) return;
        const label = {group, join: sep === '\n\n' ? 'LF LF' : 'CRLF CRLF', nbsp, mask, index, address};
        matches.push(label);
        fs.writeFileSync(path.join(__dirname, `FOUND-br-${group}-${mask}-${index}.txt`), bytes);
      });
    }
    console.log(family, perFamily[family]);
  }
}
assert.equal(generated, 12288);
const result = {
  started, finished: new Date().toISOString(),
  selftests: ['Solved Stage One entropy at index 0', 'Grycoin Block 1 full answer at index 0'],
  source: {file: 'wattpad-paragraphs.json', sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(L.ROOT, 'wattpad-paragraphs.json'))).digest('hex')},
  family: 'All 1024 internal-break deletion masks x raw/three/four groups x LF LF/CRLF CRLF x NBSP keep/space',
  streamFormat: 'Each candidate UTF8 preceded by unsigned 32-bit big-endian byte length; order groups raw,three,four; joins LF,CRLF; NBSP keep,space; masks 0..1023',
  candidateStreamSha256: stream.digest('hex'), generated, uniqueMd5Tested: tested,
  addressChecks: checks, targetComparisons: checks * 2,
  indices: [0,1,2,3,4,5,6], targets: [L.PRIZE,L.SUPERSEDED], perFamily, matches,
  assertions: ['273 paragraphs', '10 original internal LF', '6 original NBSP', '10-popcount retained internal LF', '544 separator LF plus retained internal LF', 'no CRCRLF', 'canonical CRLF or LF'],
};
fs.writeFileSync(path.join(__dirname, 'br-deletion-results.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({generated, tested, checks, matches: matches.length, stream:result.candidateStreamSha256}));
