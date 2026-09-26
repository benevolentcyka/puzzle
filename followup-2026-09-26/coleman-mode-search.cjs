'use strict';
// Test a specific Ian Coleman UI setting mistake: fixed mnemonic length hashes
// the ASCII entropy string before converting it to BIP39, unlike raw mode.
// Run from anywhere: node followup-2026-09-26/coleman-mode-search.cjs
// Results contain counts and hashes, never spendable keys or winning text.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const L = require('../followup-2026-09-25/lib.cjs');
const V = require('../verifier.cjs');
L.selftest(); V.selftest();
const started = new Date().toISOString();
const paragraphs = L.chapterParagraphs();
const targets = new Set([L.PRIZE, L.SUPERSEDED]);
const digest = crypto.createHash('sha256');
const texts = new Map();
const groups = Object.values(L.GROUPS);

// Use all 16 planted-group selections, three heading boundaries, and the
// serialization ambiguities grounded in the saved chapter. Every byte source
// is reconstructed here, rather than read from Git-normalized base files.
for (let mask = 0; mask < 16; mask++) {
  for (const start of [0, 1, 3]) for (const spaces of ['keep', 'nbsp-space', 'trim']) {
    for (const sep of ['\n\n', '\r\n\r\n']) for (const tail of ['', sep.slice(0, sep.length / 2)]) {
      const text = paragraphs.slice(start).map((p, j) => {
        const i = start + j;
        if (groups.some((g, k) => ((mask >>> k) & 1) && g.includes(i))) p = L.flip(p);
        if (spaces !== 'keep') p = p.replace(/\u00a0/g, ' ');
        if (spaces === 'trim') p = p.trim();
        // Genuine within-paragraph breaks and full paragraph joins are distinct.
        return p.replace(/\r\n|\r|\n/g, sep === '\n\n' ? '\n' : '\r\n');
      }).join(sep) + tail;
      const md5 = L.md5(Buffer.from(text, 'utf8')).toString('hex');
      if (!texts.has(md5)) texts.set(md5, {
        mask, start, spaces, separator: JSON.stringify(sep), tail: JSON.stringify(tail), text,
      });
    }
  }
}

let derivations = 0, addresses = 0;
const byMode = {};
const indices = 7; // 0 through 6; author's original funded key was the first.
function check(entropy, mode, md5, label) {
  digest.update(`${mode}:${md5}:${entropy.toString('hex')}\n`);
  const addrs = L.bip44Addresses(entropy, indices);
  derivations++; addresses += addrs.length;
  byMode[mode] = (byMode[mode] || 0) + 1;
  const index = addrs.findIndex(a => targets.has(a));
  if (index >= 0) {
    const witness = path.join(__dirname, `FOUND-coleman-${Date.now()}.txt`);
    fs.writeFileSync(witness, label.text, 'utf8');
    console.log(`MATCH ${mode} ${addrs[index]} index=${index}; local witness ${witness}`);
    return {mode, md5, index, address: addrs[index], witness};
  }
  return null;
}
const hits = [];
let checkedTexts = 0;
for (const [md5, label] of texts) {
  // Baseline first: it shares the same serialization generator as new modes.
  const raw = check(Buffer.from(md5, 'hex'), 'raw-128', md5, label);
  if (raw) hits.push(raw);
  for (const letterCase of ['lower', 'upper']) {
    const clean = letterCase === 'upper' ? md5.toUpperCase() : md5;
    const hashed = L.sha256(Buffer.from(clean, 'utf8'));
    for (const bytes of [16, 20, 24, 28, 32]) {
      const hit = check(hashed.subarray(0, bytes), `fixed-${bytes * 8}-${letterCase}`, md5, label);
      if (hit) hits.push(hit);
    }
  }
  checkedTexts++;
  if (checkedTexts % 100 === 0) console.log(`texts=${checkedTexts}/${texts.size}; addresses=${addresses}`);
}
const report = {
  complete: true,
  status: hits.length ? 'match-found-see-local-witness' : 'no-match-in-stated-family',
  started_utc: started, finished_utc: new Date().toISOString(),
  source_sha256: L.sha256(fs.readFileSync(path.join(L.ROOT, 'wattpad-paragraphs.json'))).toString('hex'),
  target_addresses: [...targets], text_variants: texts.size, derivations, addresses,
  bip44_indices: [0, 6], passphrase: '', byMode,
  candidate_stream_sha256: digest.digest('hex'), hit_count: hits.length,
};
fs.writeFileSync(path.join(__dirname, 'coleman-mode-results.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
