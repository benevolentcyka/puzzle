'use strict';
// Calibration target: Grycoin Block 2 (reddit.com/r/Grycoin/comments/cleczc), Aoi's "simple example
// for the format used in both phases of block 77". It was solved and swept by puzzleponky on
// 2019-08-03 (tx 351371588afd..., to 129jw1GUGwiJbf4rL7qEANPbxvSRC5zfHN), and 7 minutes later the
// same person swept Stage One. Published filters: MD5 prefix 3c6; payout 1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi.
// Every family below checks the MD5 prefix first, then derives BIP44 addresses for survivors.
//   node example-block-search.cjs            # all families (about 5 minutes)
//   node example-block-search.cjs flips20    # one family
//   node example-block-search.cjs --write-bases   # write inputs for md5-toggle-search.c
const fs = require('fs');
const path = require('path');
const L = require('./lib.cjs');

L.selftest();
const P = L.exampleParagraphs();
const FFWW = [2, 3, 6, 7];
const SEPS = ['\n\n', '\r\n\r\n'];
let tested = 0, survivors = 0;
const hits = [];

function check(text, label, indices = 2) {
  tested++;
  const h = L.md5(Buffer.from(text, 'latin1'));
  if (!L.hasPrefix3c6(h)) return;
  survivors++;
  const addrs = L.bip44Addresses(h, indices);
  const i = addrs.indexOf(L.EXAMPLE);
  if (i >= 0) { hits.push({label, index: i, md5: h.toString('hex'), text}); console.log('HIT', label, i); }
}
// Byte offsets of each paragraph's first and last letter for a given separator.
function boundaryOffsets(paras, sep) {
  const pos = []; let off = 0;
  for (const p of paras) {
    pos.push(off + [...p].findIndex(L.isLetter), off + [...p].findLastIndex(L.isLetter));
    off += p.length + sep.length;
  }
  return pos;
}
function toggled(base, positions, mask) {
  const b = Buffer.from(base);
  for (let i = 0; i < positions.length; i++) if ((mask >> i) & 1) b[positions[i]] ^= 32;
  return b.toString('latin1');
}

const families = {
  // Every subset of toggles on the 20 paragraph-boundary letters; BIP44 indices 0-19.
  flips20() {
    for (const sep of SEPS) {
      const base = Buffer.from(P.join(sep), 'latin1'), pos = boundaryOffsets(P, sep);
      for (let m = 0; m < 1 << 20; m++) check(toggled(base, pos, m), `flips20 ${JSON.stringify(sep)} ${m}`, 20);
    }
  },
  // Draft hypotheses from the "himself" inconsistency: the sentence "Even after I explained..."
  // absent, or a separate paragraph; every boundary-toggle subset; four separators.
  drafts() {
    const extra = ' Even after I explained the method used and the result in detail.';
    const drafts = {
      removed: P.map(p => p.replace(extra, '')),
      split: P.flatMap(p => p.includes(extra) ? [p.replace(extra, ''), extra.trim()] : [p]),
    };
    for (const [name, paras] of Object.entries(drafts)) for (const sep of ['\n\n', '\r\n\r\n', '\n', '\r\n']) {
      const base = Buffer.from(paras.join(sep), 'latin1'), pos = boundaryOffsets(paras, sep);
      for (let m = 0; m < 1 << pos.length; m++) check(toggled(base, pos, m), `drafts ${name} ${JSON.stringify(sep)} ${m}`);
    }
  },
  // Trailing spaces (dropped by Reddit's rich-text editor) after any subset of paragraphs.
  trailingSpaces() {
    const sets = [[2, 3, 6, 7], [2, 3, 5, 6, 7], [2, 3, 4, 6, 7], [2, 3, 4, 5, 6, 7], []];
    for (const set of sets) for (const mode of ['lu', 'nu', 'ln']) for (const sep of SEPS)
      for (let t = 0; t < 1 << 10; t++) for (const lead of ['', ' '])
        check(lead + P.map((p, i) => (set.includes(i) ? L.flip(p, mode) : p) + ((t >> i) & 1 ? ' ' : '')).join(sep),
          `trailing ${set} ${mode} ${t}`);
  },
  // Sentences added after hashing: any non-first sentence or non-sign paragraph absent.
  sentenceEdits() {
    const S = P.map(p => p.split(/(?<=[.?!]"?) (?=[A-Z])/));
    const opts = S.map((s, i) => {
      const o = [];
      for (let m = 0; m < 1 << (s.length - 1); m++) o.push([s[0], ...s.slice(1).filter((_, j) => (m >> j) & 1)].join(' '));
      if (!FFWW.includes(i)) o.push(null);
      return o;
    });
    const walk = (i, acc) => {
      if (i === opts.length) {
        const paras = acc.filter(x => x !== null);
        for (const mode of ['lu', 'nu', 'ln']) for (const sep of SEPS)
          check(paras.map(p => /^[SATOHIM]/i.test(p.match(/[A-Za-z]/)[0]) ? p : L.flip(p, mode)).join(sep), 'sentenceEdits');
        return;
      }
      for (const o of opts[i]) walk(i + 1, [...acc, o]);
    };
    walk(0, []);
  },
  // FFWW (several flip modes) plus one or two arbitrary letter toggles anywhere.
  ffwwPlus2() {
    for (const sep of SEPS) {
      const text = P.join(sep), pos = boundaryOffsets(P, sep);
      const letters = [...text].flatMap((c, i) => L.isLetter(c) ? [i] : []);
      for (const [name, set, mode] of [['lu', FFWW, 'lu'], ['lt', FFWW, 'lt'], ['o-lu', [2, 3, 5, 6, 7], 'lu'], ['nu', FFWW, 'nu'], ['ln', FFWW, 'ln']]) {
        const b = Buffer.from(text, 'latin1');
        for (const i of set) {
          if (mode[0] === 'l') b[pos[2 * i]] |= 32;
          if (mode[1] === 'u') b[pos[2 * i + 1]] &= ~32; else if (mode[1] === 't') b[pos[2 * i + 1]] ^= 32;
        }
        for (let x = 0; x < letters.length; x++) {
          b[letters[x]] ^= 32; check(b.toString('latin1'), `ffwwPlus2 ${name} ${x}`);
          for (let y = x + 1; y < letters.length; y++) {
            b[letters[y]] ^= 32; check(b.toString('latin1'), `ffwwPlus2 ${name} ${x} ${y}`); b[letters[y]] ^= 32;
          }
          b[letters[x]] ^= 32;
        }
      }
    }
  },
  // Per paragraph: unflipped, or first letter changed plus the last letter of any one sentence
  // (covers Aoi's own "himself" -> "himselF" example).
  sentenceLastLetter() {
    const lastCands = p => {
      const c = [...p], out = new Set([c.findLastIndex(L.isLetter)]);
      for (let i = 0; i < c.length; i++) if (/[.?!]/.test(c[i])) { let j = i - 1; while (j >= 0 && c[j] === '"') j--; if (j >= 0 && L.isLetter(c[j])) out.add(j); }
      return [...out];
    };
    const LC = P.map(lastCands);
    const walk = (i, acc) => {
      if (i === P.length) {
        for (const fm of ['l', 't', 'n']) for (const lm of ['u', 't']) for (const sep of SEPS)
          check(P.map((p, k) => {
            if (acc[k] === null) return p;
            const c = [...p], a = c.findIndex(L.isLetter);
            if (fm === 'l') c[a] = c[a].toLowerCase(); else if (fm === 't') c[a] = L.toggle(c[a]);
            c[acc[k]] = lm === 'u' ? c[acc[k]].toUpperCase() : L.toggle(c[acc[k]]);
            return c.join('');
          }).join(sep), 'sentenceLastLetter');
        return;
      }
      for (const o of [null, ...LC[i]]) walk(i + 1, [...acc, o]);
    };
    walk(0, []);
  },
  // Some of the doubled line breaks missed (as happened 10 times in the Wattpad chapter).
  missedBreaks() {
    for (let fm = 0; fm < 1 << 20; fm++) {
      if (fm & ~0xFFF0) continue; // boundary toggles on paragraphs 2-7 only
      const ps = P.map((p, i) => {
        const c = [...p], a = c.findIndex(L.isLetter), z = c.findLastIndex(L.isLetter);
        if ((fm >> (2 * i)) & 1) c[a] = L.toggle(c[a]);
        if ((fm >> (2 * i + 1)) & 1) c[z] = L.toggle(c[z]);
        return c.join('');
      });
      for (const [dbl, sgl] of [['\n\n', '\n'], ['\r\n\r\n', '\r\n'], ['\n\n', '\n\n\n']])
        for (let sm = 1; sm < 1 << 9; sm++) {
          let out = ps[0];
          for (let i = 1; i < 10; i++) out += ((sm >> (i - 1)) & 1 ? sgl : dbl) + ps[i];
          check(out, `missedBreaks ${fm} ${sm}`);
        }
    }
  },
  // One inserted or deleted character anywhere, with every subset of the 8 FFWW flips.
  insertDelete() {
    for (const sep of SEPS) {
      const base = Buffer.from(P.join(sep), 'latin1'), pos = boundaryOffsets(P, sep);
      const fpos = FFWW.flatMap(i => [pos[2 * i], pos[2 * i + 1]]);
      for (let fm = 0; fm < 256; fm++) {
        const s = toggled(base, fpos, fm);
        for (let i = 0; i < s.length; i++) {
          check(s.slice(0, i) + s.slice(i + 1), 'delete');
          for (const c of [' ', '\n', '.', '"', "'", '\r\n']) check(s.slice(0, i) + c + s.slice(i), 'insert');
        }
      }
    }
  },
  // Double spaces after sentences (collapsed by Reddit's editor), every subset.
  doubleSpaces() {
    for (const [set, mode] of [[FFWW, 'lu'], [[2, 3, 5, 6, 7], 'lu'], [FFWW, 'nu'], [[], 'lu'], [[2, 3, 4, 6, 7], 'lu']])
      for (const sep of SEPS) {
        const t = P.map((p, i) => set.includes(i) ? L.flip(p, mode) : p).join(sep);
        const gaps = [...t].flatMap((c, i) => c === ' ' && /[.?!"]/.test(t[i - 1]) && /[A-Z"]/.test(t[i + 1]) ? [i] : []);
        for (let m = 0; m < 1 << gaps.length; m++) {
          let out = '', last = 0;
          gaps.forEach((g, k) => { if ((m >> k) & 1) { out += t.slice(last, g) + ' '; last = g; } });
          check(out + t.slice(last), 'doubleSpaces');
        }
      }
  },
};

if (process.argv[2] === '--write-bases') {
  // FFWW-flipped base texts and letter offsets for md5-toggle-search.c.
  for (const [name, sep] of [['lf', '\n\n'], ['crlf', '\r\n\r\n']]) {
    const b = Buffer.from(P.map((p, i) => FFWW.includes(i) ? L.flip(p) : p).join(sep), 'latin1');
    fs.writeFileSync(path.join(__dirname, `example-ffww-${name}.bin`), b);
    fs.writeFileSync(path.join(__dirname, `example-letters-${name}.txt`),
      [...b].flatMap((x, i) => L.isLetter(String.fromCharCode(x)) ? [i] : []).join('\n'));
  }
  console.log('wrote example-ffww-{lf,crlf}.bin and example-letters-{lf,crlf}.txt');
} else {
  const names = process.argv[2] ? [process.argv[2]] : Object.keys(families);
  for (const n of names) {
    const t0 = tested, s0 = survivors;
    families[n]();
    console.log(JSON.stringify({family: n, tested: tested - t0, prefix3c6: survivors - s0}));
  }
  console.log(JSON.stringify({tested, prefix3c6: survivors, hits: hits.length}));
  if (hits.length) fs.writeFileSync(path.join(__dirname, 'EXAMPLE-HIT.json'), JSON.stringify(hits, null, 2));
}
