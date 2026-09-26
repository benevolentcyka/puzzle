'use strict';
// Real Big Block: families of "Second" chapter serializations not covered (or only lightly covered)
// by earlier ledgers, checked against the live prize and the superseded 2019-07-22 escrow.
//   node chapter-variants.cjs            # all families (about 5 minutes on 4 cores)
//   node chapter-variants.cjs brPromote  # one family
const fs = require('fs');
const path = require('path');
const L = require('./lib.cjs');

L.selftest();
const PARAS = L.chapterParagraphs();
const G = L.GROUPS;
const G123 = [...G.g1, ...G.g2, ...G.g3], G1234 = [...G123, ...G.g4];
const TARGETS = new Set([L.PRIZE, L.SUPERSEDED]);
const INDICES = 21; // the public ledger derived 0-5; Aoi pointed at the 7th key (index 6) on 2019-07-28
const seen = new Set();
const hits = [];
let tested = 0;

function test(text, label, paths = null) {
  if (seen.has(text)) return;
  seen.add(text); tested++;
  const root = L.master(L.seed(L.mnemonic(L.md5(Buffer.from(text, 'utf8')))));
  const account = L.derivePath(root, "m/44'/0'/0'/0");
  for (let i = 0; i < INDICES; i++) {
    const a = L.address(L.child(account, i).key);
    if (TARGETS.has(a)) report(label, `m/44'/0'/0'/0/${i}`, a, text);
  }
  for (const p of paths || []) {
    const node = L.derivePath(root, p);
    for (let i = 0; i < 10; i++) for (const comp of [true, false]) {
      const a = L.address(L.child(node, i).key, comp);
      if (TARGETS.has(a)) report(label, `${p}/${i}${comp ? '' : ' uncompressed'}`, a, text);
    }
  }
}
function report(label, where, a, text) {
  hits.push({label, where, address: a});
  console.log('HIT', label, where, a);
  fs.writeFileSync(path.join(__dirname, `FOUND-${Date.now()}.txt`), text); // FOUND-* is gitignored
}
const nbspModes = {keep: p => p, sp: p => p.replace(/\xa0/g, ' '), drop: p => p.replace(/\xa0 /g, ' ')};
function build(set, {mode = 'lu', nbsp = 'keep', sep = '\n\n', map = null} = {}) {
  const brj = sep.startsWith('\r') ? '\r\n' : '\n';
  return PARAS.map((p, i) => {
    let q = map ? map(p, i) : p;
    if (set.has(i)) q = L.flip(q, mode);
    // Normalize existing pairs first: maps may already introduce CRLF joins.
    return nbspModes[nbsp](q).replace(/\r\n|\r|\n/g, brj);
  }).join(sep);
}
const COMBOS = (() => {
  const out = {none: []};
  const names = ['g1', 'g2', 'g3', 'g4'];
  for (let m = 1; m < 16; m++) out[names.filter((_, k) => (m >> k) & 1).join('')] = names.filter((_, k) => (m >> k) & 1).flatMap(n => G[n]);
  return out;
})();

const families = {
  // All 16 group combinations x NBSP handling x four joins x trailing newline, indices 0-20.
  groupsWideIndex() {
    for (const [cn, s] of Object.entries(COMBOS)) for (const nbsp of Object.keys(nbspModes))
      for (const sep of ['\n\n', '\r\n\r\n', '\n', '\r\n']) for (const tail of ['', '\n', '\r\n'])
        test(build(new Set(s), {nbsp, sep}) + tail, `groups ${cn} ${nbsp} ${JSON.stringify(sep)} ${JSON.stringify(tail)}`);
  },
  // Chapter-wide letter-set rules, including Aoi's 2019-07-28 wording "not starting with a letter in
  // 'Satoshi'" (SATOHI) and SATOSHI+THOMAS (SATOHIM); groups plus preceding "I" paragraphs; the
  // hand-bolded heading "b) THOMAS and Satoshi" flipped or edited.
  letterRules() {
    const first = p => (p.match(/[A-Za-z]/) || [''])[0].toUpperCase();
    const rule = letters => PARAS.map((_, i) => i).filter(i => first(PARAS[i]) && !letters.includes(first(PARAS[i])));
    const rules = {
      itasm: rule('ITASM'), satohim: rule('SATOHIM'), satohi: rule('SATOHI'),
      g123I: [...G123, 3, 91, 164, 165, 166], g1234I: [...G1234, 3, 91, 164, 165, 166, 233],
      g123hd: [...G123, 181], g1234hd: [...G1234, 181],
    };
    const heads = {orig: null, satosh: 'b) THOMAS and Satosh', satoshI: 'b) THOMAS and SatoshI', SATOSHI: 'b) THOMAS and SATOSHI'};
    for (const [rn, s] of Object.entries(rules)) for (const [hn, hv] of Object.entries(heads)) {
      if (hn !== 'orig' && !rn.startsWith('g')) continue;
      for (const mode of ['lu', 'tt', 'lt']) for (const nbsp of ['keep', 'sp']) for (const sep of ['\n\n', '\r\n\r\n']) for (const tail of ['', '\n'])
        test(build(new Set(s), {mode, nbsp, sep, map: (p, i) => i === 181 && hv ? hv : p}) + tail, `rule ${rn} ${hn} ${mode}`);
    }
  },
  // Every subset of the 10 in-paragraph <br> breaks promoted to full paragraph breaks
  // (Aoi: "two line breaks between each of them").
  brPromote() {
    const br = PARAS.map((p, i) => p.includes('\n') ? i : -1).filter(i => i >= 0);
    for (const [cn, s] of [['g123', G123], ['g1234', G1234], ['none', []]]) for (const nbsp of ['keep', 'sp'])
      for (const sep of ['\n\n', '\r\n\r\n']) for (let m = 1; m < 1 << br.length; m++)
        test(build(new Set(s), {nbsp, sep, map: (p, i) => br.includes(i) && (m >> br.indexOf(i)) & 1 ? p.replace(/\n/g, sep) : p}), `br ${cn} ${m}`);
  },
  // Trailing spaces stripped (rendered or tablet copy), NBSP normalised three ways.
  stripped() {
    const tr = {end: p => p.replace(/ +$/, ''), endBr: p => p.replace(/ +$/, '').replace(/ +\n/g, '\n')};
    const nb = {keep: p => p, sp: p => p.replace(/\xa0/g, ' '), one: p => p.replace(/\xa0 /g, ' ').replace(/ {2,}/g, ' ')};
    for (const [cn, s] of [['none', []], ['g123', G123], ['g1234', G1234]]) for (const t of Object.values(tr)) for (const n of Object.values(nb))
      for (const sep of ['\n\n', '\r\n\r\n', '\n', '\r\n']) for (const tail of ['', '\n'])
        test(build(new Set(s), {sep, map: p => t(n(p))}) + tail, `stripped ${cn}`);
  },
  // Input-length truncation by a hash tool or text field at common limits.
  truncated() {
    const limits = [1000, 1024, 2000, 2048, 4000, 4096, 5000, 8000, 8192, 10000, 15000, 16000, 16383, 16384, 20000,
      24576, 25000, 30000, 32000, 32767, 32768, 40000, 45000];
    for (const [cn, s] of [['none', []], ['g123', G123], ['g1234', G1234]]) for (const nbsp of ['keep', 'sp']) for (const sep of ['\n\n', '\r\n\r\n']) {
      const full = build(new Set(s), {nbsp, sep});
      for (const n of limits) test(full.slice(0, n), `truncated ${cn} ${n}`);
    }
  },
  // Aoi's own twist repertoire: quotation marks around the answer (block 42, password-manager
  // chapter), repetition, brackets, title/heading changes, reversed paragraph order.
  twists() {
    const headings = new Set(PARAS.map((_, i) => i).filter(i => /^(Second|I\. |II\. |III\. |\d\. |[a-f]\) |Abstract)/.test(PARAS[i]) && PARAS[i].length < 80));
    for (const [cn, s] of [['none', []], ['g123', G123], ['g1234', G1234]]) for (const nbsp of ['keep', 'sp']) for (const sep of ['\n\n', '\r\n\r\n', '\n']) {
      const brj = sep.startsWith('\r') ? '\r\n' : '\n';
      const ps = PARAS.map((p, i) => nbspModes[nbsp](new Set(s).has(i) ? L.flip(p) : p).replace(/\n/g, brj));
      const t = ps.join(sep);
      for (const [tn, v] of Object.entries({
        quotes: `"${t}"`, squotes: `'${t}'`, repeat: t + t, repeatSpace: `${t} ${t}`, brackets: `[${t}]`,
        titleSecond: `Second${sep}${t}`, finalVersion: `Final version${sep}${t}`,
        reversed: [...ps].reverse().join(sep), dropTitle: ps.slice(1).join(sep), dropHeadings: ps.filter((_, i) => !headings.has(i)).join(sep),
      })) test(v, `twist ${cn} ${tn}`);
    }
  },
  // Non-BIP44 paths from Ian Coleman's tool (BIP32 client presets, change chain, other accounts),
  // compressed and uncompressed.
  otherPaths() {
    const paths = ["m/0", "m/0'/0", "m/0'/0'", "m/44'/0'/0'/1", "m/44'/0'/1'/0", "m/44'/0'/2'/0", "m/44'/1'/0'/0", "m/44'/0'/0'", "m/0'"];
    for (const [cn, s] of [['none', []], ['g123', G123], ['g1234', G1234], ['g4', G.g4]]) for (const nbsp of ['keep', 'sp'])
      for (const sep of ['\n\n', '\r\n\r\n', '\n', '\r\n']) for (const tail of ['', '\n']) {
        const t = build(new Set(s), {nbsp, sep}) + tail;
        seen.delete(t); // re-test with extra paths even if an earlier family saw this text
        test(t, `paths ${cn}`, paths);
      }
  },
};

const names = process.argv[2] ? [process.argv[2]] : Object.keys(families);
for (const n of names) {
  const t0 = tested;
  families[n]();
  console.log(JSON.stringify({family: n, texts: tested - t0}));
}
console.log(JSON.stringify({texts: tested, hits: hits.length}));
