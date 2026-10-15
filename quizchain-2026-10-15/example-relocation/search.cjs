'use strict';
// Offline finite draft reconstruction. No network, signing, or transactions.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('assert');

const args = process.argv.slice(2);
let repo = 'C:\\Users\\boomb\\Downloads\\puzzle-investigation';
let output = __dirname;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--repo' && args[i + 1]) repo = path.resolve(args[++i]);
  else if (args[i] === '--output' && args[i + 1]) output = path.resolve(args[++i]);
  else throw new Error('Usage: node search.cjs [--repo PATH] [--output PATH]');
}
const sha256 = b => crypto.createHash('sha256').update(b).digest('hex');
const L = require(path.join(repo, 'followup-2026-09-25/lib.cjs'));
const V = require(path.join(repo, 'verifier.cjs'));
L.selftest();
V.selftest();
const targets = [L.EXAMPLE, L.PRIZE, L.SUPERSEDED];
const original = L.exampleParagraphs();
const question = Buffer.from(original.join('\n\n'));
assert.strictEqual(original.length, 10);
assert.strictEqual(question.length, 1549);
assert.strictEqual(L.md5(question).toString('hex'), '7759227d7406d8230d7e3a8f7b9846d7');
const sentence = 'Even after I explained the method used and the result in detail.';
assert(original[4].endsWith(' ' + sentence));
assert.strictEqual(original.filter(p => p.includes(sentence)).length, 1);
const stripped = original.map((p, i) => i === 4 ? p.slice(0, -sentence.length - 1) : p);

// 19 attachments plus 11 standalone placements; skip only the published original.
const layouts = [];
for (let paragraph = 0; paragraph < 10; paragraph++) for (const side of ['before', 'after']) {
  if (paragraph === 4 && side === 'after') continue;
  const paras = stripped.slice();
  paras[paragraph] = side === 'before' ? sentence + ' ' + paras[paragraph] : paras[paragraph] + ' ' + sentence;
  layouts.push({id: `attach-${paragraph}-${side}`, kind: 'attach', paragraph, side, paras});
}
for (let at = 0; at <= 10; at++) {
  const paras = stripped.slice();
  paras.splice(at, 0, sentence);
  layouts.push({id: `standalone-${at}`, kind: 'standalone', insertion_index: at, paras});
}
assert.strictEqual(layouts.length, 30);
const rules = ['raw', 'ffww', 'non-satoshi', 'named', 'ffww-named', 'non-satoshi-named'];
const modes = ['lu', 'tt'];
const joins = ['\n\n', '\r\n\r\n', '\n', '\r\n'];
const sourceHashes = Object.fromEntries([
  'aoi-posts-archive.json', 'english.txt', 'followup-2026-09-25/lib.cjs', 'verifier.cjs',
].map(f => [f, sha256(fs.readFileSync(path.join(repo, f)))]));
const configuration = {
  family: 'relocate-exact-Even-after-sentence-v1',
  source_question_md5: L.md5(question).toString('hex'),
  source_question_sha256: sha256(question),
  source_files_sha256: sourceHashes,
  runner_sha256: sha256(fs.readFileSync(__filename)),
  sentence, removed_from_zero_based_paragraph: 4,
  removal: 'Remove the exact terminal sentence and its one preceding ASCII space.',
  layouts: layouts.map(({paras, ...descriptor}) => descriptor),
  rule_definitions: {
    raw: 'No selected paragraph endpoints.',
    ffww: 'Select paragraphs whose current first ASCII letter is F or W.',
    'non-satoshi': 'Select paragraphs whose current first ASCII letter is absent from SATOSHI.',
    named: 'Lowercase the I of the original I expected otherwise sentence wherever relocation places it; uppercase the f of its himself.',
    'ffww-named': 'Apply ffww, then named.',
    'non-satoshi-named': 'Apply non-satoshi, then named.',
  },
  rules,
  modes: {lu: 'Lowercase first and uppercase last ASCII letter of selected paragraphs.', tt: 'Toggle both selected paragraph endpoints.'},
  join_hex: joins.map(s => Buffer.from(s).toString('hex')),
  final_newline: false,
  layout_whitespace: 'One ASCII space when attaching to a paragraph; selected global join when standalone. Other text stays unchanged.',
  derivation: 'UTF-8 -> raw 16-byte MD5 -> English BIP39 -> empty passphrase -> BIP32 compressed P2PKH',
  path: "m/44'/0'/0'/0/i", indices: [0, 1, 2, 3, 4, 5, 6], targets,
  prefix_filter_used: false,
  enumeration_order: 'layouts, rules, modes, joins, each in manifest order; retain first exact-text occurrence.',
  candidate_stream: 'For each distinct exact UTF-8 text: unsigned 32-bit big-endian length then text bytes.',
};
fs.mkdirSync(output, {recursive: true});
fs.writeFileSync(path.join(output, 'plan.json'), JSON.stringify(configuration, null, 2) + '\n');
const texts = new Map();
let operations = 0;
for (const layout of layouts) for (const rule of rules) for (const mode of modes) for (const sep of joins) {
  const paras = layout.paras.map(p => {
    const first = p.match(/[A-Za-z]/)[0];
    const selected = rule.startsWith('ffww') ? 'FW'.includes(first)
      : rule.startsWith('non-satoshi') ? !'SATOSHI'.includes(first) : false;
    let text = selected ? L.flip(p, mode) : p;
    const namedEnd = text.search(/post outing himsel[fF]\./);
    if (rule.includes('named') && namedEnd >= 0) {
      const chars = [...text];
      const namedStart = text.search(/[Ii] expected otherwise/);
      assert(namedStart >= 0);
      chars[namedStart] = 'i';
      chars[namedEnd + 'post outing himself'.length - 1] = 'F';
      text = chars.join('');
    }
    assert.strictEqual(text.toLowerCase(), p.toLowerCase(), 'Case operation changed a non-case byte');
    return text;
  });
  const text = paras.join(sep);
  operations++;
  if (!texts.has(text)) texts.set(text, {layout: layout.id, rule, mode, join_hex: Buffer.from(sep).toString('hex')});
}
const stream = crypto.createHash('sha256');
let addresses = 0, prefix = 0, comparisons = 0;
const matches = [];
const begin = Date.now();
for (const [text, label] of texts) {
  const bytes = Buffer.from(text), md5 = L.md5(bytes), len = Buffer.alloc(4);
  len.writeUInt32BE(bytes.length);
  stream.update(len).update(bytes);
  if (L.hasPrefix3c6(md5)) prefix++;
  const primary = L.bip44Addresses(md5, 7);
  const independent = V.derivationFromBytes(bytes, 7);
  assert.deepStrictEqual(primary, independent.children.map(c => c.address));
  comparisons += 7;
  addresses += primary.length;
  for (const target of targets) if (primary.includes(target)) {
    const index = primary.indexOf(target);
    const filename = `FOUND-example-relocation-${matches.length + 1}`;
    // Only these local FOUND files may contain successful input/key material.
    fs.writeFileSync(path.join(output, filename + '.txt'), bytes);
    fs.writeFileSync(path.join(output, filename + '.json'), JSON.stringify({
      target, index, label, md5: md5.toString('hex'), mnemonic: independent.mnemonic,
      private_wif: independent.children[index].wif,
      source_configuration_sha256: sha256(Buffer.from(JSON.stringify(configuration))),
    }, null, 2) + '\n');
    matches.push({target, index, file: filename});
  }
}
const result = {
  configuration, complete: true, elapsed_seconds: (Date.now() - begin) / 1000,
  selftests: ['Known raw example MD5 and length', 'Stage One address', 'Grycoin Block 1 address', 'Author published WIF vector'],
  layouts: layouts.length, enumeration_operations: operations,
  distinct_exact_texts: texts.size, address_derivation_operations: addresses,
  independent_address_comparisons: comparisons, target_comparisons: addresses * targets.length,
  prefix3c6_candidates: prefix, matches,
  candidate_stream_sha256: stream.digest('hex'), finished_utc: new Date().toISOString(),
};
fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({complete: true, distinct_exact_texts: texts.size, addresses, independent_address_comparisons: comparisons,
  prefix3c6_candidates: prefix, matches: matches.length, candidate_stream_sha256: result.candidate_stream_sha256}));
