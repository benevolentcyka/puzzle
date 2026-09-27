'use strict';
// Execute the preserved 2019 converter, including its short-entropy behavior.
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'followup-2026-09-26/verification');
class Integer {
  constructor(x) { this.n = BigInt(x); }
  add(x) { return new Integer(this.n + x.n); }
  multiply(x) { return new Integer(this.n * x.n); }
  pow(x) { return new Integer(this.n ** BigInt(x)); }
  toString(base) { return this.n.toString(base); }
  static parse(x) { return new Integer(x); }
}
Integer.ZERO = new Integer(0);
function bytes(words) {
  const b = Buffer.alloc(words.length * 4);
  words.forEach((w, i) => b.writeUInt32BE(w >>> 0, i * 4));
  return b;
}
const sandbox = {window: {}, BigInteger: Integer,
  WORDLISTS: {english: JSON.parse(fs.readFileSync(path.join(dir, 'languages/english.json'))).words},
  sjcl: {hash: {sha256: {hash: words => crypto.createHash('sha256').update(bytes(words)).digest()}},
         codec: {hex: {fromBits: b => b.toString('hex')}}}};
vm.createContext(sandbox);
for (const file of ['iancoleman-2019-entropy.js', 'iancoleman-2019-jsbip39.js']) {
  vm.runInContext(fs.readFileSync(path.join(dir, file), 'utf8'), sandbox, {filename: file});
}
const converter = new sandbox.Mnemonic('english');
const inputs = JSON.parse(fs.readFileSync(0, 'utf8'));
const output = inputs.map(input => {
  const parsed = sandbox.window.Entropy.fromString(input);
  const n = Math.floor(parsed.binaryStr.length / 32) * 32;
  const bits = parsed.binaryStr.slice(parsed.binaryStr.length - n);
  if (!n) return {input, base: parsed.base.str, entropy: '', words: ''};
  const raw = Buffer.from(bits.match(/.{8}/g).map(x => parseInt(x, 2)));
  const words = converter.toMnemonic([...raw]);
  if (!converter.check(words)) throw new Error('Historical mnemonic self-check failed');
  return {input, base: parsed.base.str, entropy: raw.toString('hex'), words};
});
process.stdout.write(JSON.stringify(output));
