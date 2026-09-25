'use strict';
// Independent, dependency-free verifier for Aoi Nakamoto's Quizchain.
// It only derives public addresses and prints candidate values. It never signs
// or broadcasts a transaction. Inputs may be exact UTF-8 text files or entropy.

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const WORDS = fs.readFileSync(path.join(__dirname, 'english.txt'), 'utf8').trim().split(/\r?\n/);
if (WORDS.length !== 2048) throw new Error(`BIP39 word list has ${WORDS.length} entries`);
const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const N = BigInt('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141');
const TARGETS = new Set([
  '14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W', // current 0.777 BTC output
  '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC', // superseded output
]);

function sha256(b) { return crypto.createHash('sha256').update(b).digest(); }
function hash160(b) { return crypto.createHash('ripemd160').update(sha256(b)).digest(); }
function base58check(payload) {
  const b = Buffer.concat([payload, sha256(sha256(payload)).subarray(0, 4)]);
  let x = BigInt(`0x${b.toString('hex')}`), out = '';
  while (x > 0n) { out = ALPHABET[Number(x % 58n)] + out; x /= 58n; }
  for (const byte of b) { if (byte !== 0) break; out = '1' + out; }
  return out;
}
function pubkey(priv) {
  const e = crypto.createECDH('secp256k1');
  e.setPrivateKey(priv);
  return e.getPublicKey(null, 'compressed');
}
function mnemonic(entropy) {
  if (entropy.length !== 16) throw new Error('Expected 16-byte MD5 entropy');
  const bits = [...entropy].map(x => x.toString(2).padStart(8, '0')).join('')
    + sha256(entropy)[0].toString(2).padStart(8, '0').slice(0, 4);
  return Array.from({length: 12}, (_, i) => WORDS[parseInt(bits.slice(i * 11, i * 11 + 11), 2)]).join(' ');
}
function seedFromMnemonic(words, passphrase = '') {
  return crypto.pbkdf2Sync(words.normalize('NFKD'), ('mnemonic' + passphrase).normalize('NFKD'), 2048, 64, 'sha512');
}
function child(node, index, hardened = false) {
  const num = index + (hardened ? 0x80000000 : 0);
  const bytes = Buffer.alloc(4); bytes.writeUInt32BE(num);
  const message = Buffer.concat([hardened ? Buffer.concat([Buffer.from([0]), node.key]) : pubkey(node.key), bytes]);
  const h = crypto.createHmac('sha512', node.chain).update(message).digest();
  const tweak = BigInt(`0x${h.subarray(0, 32).toString('hex')}`);
  if (tweak >= N) throw new Error('Invalid BIP32 child');
  const k = (tweak + BigInt(`0x${node.key.toString('hex')}`)) % N;
  if (!k) throw new Error('Invalid BIP32 child');
  return {key: Buffer.from(k.toString(16).padStart(64, '0'), 'hex'), chain: h.subarray(32)};
}
function root(seed) {
  const h = crypto.createHmac('sha512', Buffer.from('Bitcoin seed')).update(seed).digest();
  return {key: h.subarray(0, 32), chain: h.subarray(32)};
}
function accountFromEntropy(entropy, passphrase = '') {
  let a = root(seedFromMnemonic(mnemonic(entropy), passphrase));
  for (const i of [44, 0, 0]) a = child(a, i, true);
  return child(a, 0, false);
}
function derivationFromEntropy(entropy, count = 7, passphrase = '') {
  const a = accountFromEntropy(entropy, passphrase), out = [];
  for (let i = 0; i < count; i++) {
    const c = child(a, i, false), publicKey = pubkey(c.key);
    out.push({
      index: i,
      address: base58check(Buffer.concat([Buffer.from([0]), hash160(publicKey)])),
      wif: base58check(Buffer.concat([Buffer.from([0x80]), c.key, Buffer.from([1])])),
      privateHex: c.key.toString('hex'),
    });
  }
  return {entropy: entropy.toString('hex'), mnemonic: mnemonic(entropy), children: out};
}
function derivationFromBytes(bytes, count = 7, passphrase = '') {
  return derivationFromEntropy(crypto.createHash('md5').update(bytes).digest(), count, passphrase);
}
function selftest() {
  const known = derivationFromEntropy(Buffer.from('2941774a2abec9f30c7d6777d1d53d91', 'hex'), 2);
  if (known.children[1].wif !== 'L5Z66qPmUkTAsWQywjRNHDxHrX6J1X1SQedp6V8QsbaXR7rGd6ex') {
    throw new Error(`Author calibration mismatch: ${known.children[1].wif}`);
  }
  const stage1 = derivationFromEntropy(Buffer.from('9dd2efb9bc976c2095bd534d7b8d431c', 'hex'), 1);
  if (stage1.children[0].address !== '19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN') {
    throw new Error(`Solved Stage One mismatch: ${stage1.children[0].address}`);
  }
  return 'PASS: author WIF vector and solved Stage One address';
}
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args[0] === '--selftest') console.log(selftest());
  else {
    let d;
    if (args[0] === '--file' && args[1]) d = derivationFromBytes(fs.readFileSync(args[1]), +(args[2] || 7));
    else if (args[0] === '--entropy' && args[1]) d = derivationFromEntropy(Buffer.from(args[1], 'hex'), +(args[2] || 7));
    else throw new Error('Usage: node verifier.cjs --selftest | --file PATH [count] | --entropy HEX [count]');
    console.log(JSON.stringify({...d, matches: d.children.filter(c => TARGETS.has(c.address))}, null, 2));
  }
}
module.exports = {TARGETS, mnemonic, derivationFromBytes, derivationFromEntropy, selftest};
