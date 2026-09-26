'use strict';
// Derives BIP44 addresses for the "M ... H <md5>" lines written by md5-toggle-search.c.
//   node derive-survivors.cjs out.txt [address] [indices]
const fs = require('fs');
const L = require('./lib.cjs');
L.selftest();
const [file, target = L.EXAMPLE, count = '2'] = process.argv.slice(2);
const lines = fs.readFileSync(file, 'utf8').split('\n').filter(l => l.startsWith('M ') && !l.endsWith('base'));
let hits = 0;
for (const line of lines) {
  const i = L.bip44Addresses(Buffer.from(line.split(' H ')[1], 'hex'), +count).indexOf(target);
  if (i >= 0) { hits++; console.log('HIT', line, 'index', i); }
}
console.log(JSON.stringify({survivors: lines.length, hits}));
