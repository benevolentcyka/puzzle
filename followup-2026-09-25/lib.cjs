'use strict';
// Shared helpers for the 2026-09-25 follow-up searches. Address derivation only:
// nothing here signs or broadcasts a transaction.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.join(__dirname, '..');
const WORDS = fs.readFileSync(path.join(ROOT, 'english.txt'), 'utf8').trim().split(/\r?\n/);
const B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const N = BigInt('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141');

const PRIZE = '14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W';          // live 0.777 BTC
const SUPERSEDED = '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC';     // swept by Aoi 2019-07-30
const EXAMPLE = '1tzieUfbeQghz2zjDeGHcAEfzCRgX6eLi';        // Grycoin Block 2 (cleczc), solved 2019-08-03

const sha256 = b => crypto.createHash('sha256').update(b).digest();
const md5 = b => crypto.createHash('md5').update(b).digest();
const hash160 = b => crypto.createHash('ripemd160').update(sha256(b)).digest();

function base58check(payload) {
  const b = Buffer.concat([payload, sha256(sha256(payload)).subarray(0, 4)]);
  let x = BigInt(`0x${b.toString('hex')}`), out = '';
  while (x > 0n) { out = B58[Number(x % 58n)] + out; x /= 58n; }
  for (const byte of b) { if (byte !== 0) break; out = '1' + out; }
  return out;
}
function pubkey(key, compressed = true) {
  const e = crypto.createECDH('secp256k1');
  e.setPrivateKey(key);
  return e.getPublicKey(null, compressed ? 'compressed' : 'uncompressed');
}
// BIP39 from raw entropy (Ian Coleman "raw entropy" mode). 16 bytes -> 12 words, 32 -> 24.
function mnemonic(entropy) {
  const bits = [...entropy].map(x => x.toString(2).padStart(8, '0')).join('')
    + [...sha256(entropy)].map(x => x.toString(2).padStart(8, '0')).join('').slice(0, entropy.length / 4);
  return Array.from({length: bits.length / 11}, (_, i) => WORDS[parseInt(bits.slice(i * 11, i * 11 + 11), 2)]).join(' ');
}
function seed(words, passphrase = '') {
  return crypto.pbkdf2Sync(words.normalize('NFKD'), ('mnemonic' + passphrase).normalize('NFKD'), 2048, 64, 'sha512');
}
function master(s) {
  const h = crypto.createHmac('sha512', Buffer.from('Bitcoin seed')).update(s).digest();
  return {key: h.subarray(0, 32), chain: h.subarray(32)};
}
function child(node, index, hardened = false) {
  const num = (index + (hardened ? 0x80000000 : 0)) >>> 0;
  const bytes = Buffer.alloc(4); bytes.writeUInt32BE(num);
  const data = hardened ? Buffer.concat([Buffer.from([0]), node.key]) : pubkey(node.key);
  const h = crypto.createHmac('sha512', node.chain).update(Buffer.concat([data, bytes])).digest();
  const k = (BigInt(`0x${h.subarray(0, 32).toString('hex')}`) + BigInt(`0x${node.key.toString('hex')}`)) % N;
  return {key: Buffer.from(k.toString(16).padStart(64, '0'), 'hex'), chain: h.subarray(32)};
}
function derivePath(node, p) {
  for (const s of p.split('/').slice(1)) node = child(node, parseInt(s, 10), s.endsWith("'"));
  return node;
}
function address(key, compressed = true) {
  return base58check(Buffer.concat([Buffer.from([0]), hash160(pubkey(key, compressed))]));
}
// P2PKH addresses m/44'/0'/0'/0/0..count-1 for an entropy buffer.
function bip44Addresses(entropy, count = 2, passphrase = '') {
  const account = derivePath(master(seed(mnemonic(entropy), passphrase)), "m/44'/0'/0'/0");
  return Array.from({length: count}, (_, i) => address(child(account, i).key));
}

// Grycoin Block 2 question, exactly as archived (its LF LF MD5 is Aoi's published 7759227...).
function exampleParagraphs() {
  const posts = JSON.parse(fs.readFileSync(path.join(ROOT, 'aoi-posts-archive.json'), 'utf8'));
  const text = posts.find(p => p.id === 'cleczc').selftext;
  const q = text.split('Question:\n\n')[1].split('\n\nFormat:')[0];
  if (!md5(Buffer.from(q)).toString('hex').startsWith('7759227')) throw new Error('Archived question differs');
  return q.split('\n\n');
}
function chapterParagraphs() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, 'wattpad-paragraphs.json'), 'utf8'));
}
const isLetter = c => /[A-Za-z]/.test(c);
const toggle = c => c === c.toUpperCase() ? c.toLowerCase() : c.toUpperCase();
// Stage One rule: first letter lower, last letter upper. mode[0] in l|t|n, mode[1] in u|t|n.
function flip(p, mode = 'lu') {
  const c = [...p], a = c.findIndex(isLetter), z = c.findLastIndex(isLetter);
  if (a < 0) return p;
  if (mode[0] === 'l') c[a] = c[a].toLowerCase(); else if (mode[0] === 't') c[a] = toggle(c[a]);
  if (mode[1] === 'u') c[z] = c[z].toUpperCase(); else if (mode[1] === 't') c[z] = toggle(c[z]);
  return c.join('');
}
const GROUPS = {g1: [4, 5, 6, 7], g2: [92, 93, 94, 95], g3: [167, 168, 169, 170], g4: [230, 231, 232, 234]};
const hasPrefix3c6 = h => h[0] === 0x3c && (h[1] >> 4) === 6;

function selftest() {
  // Solved Stage One (Hal Finney post, LF LF, FFWW flipped) and Grycoin Block 1 ("Still 21st Century").
  if (bip44Addresses(Buffer.from('9dd2efb9bc976c2095bd534d7b8d431c', 'hex'), 1)[0] !== '19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN')
    throw new Error('Stage One calibration failed');
  if (bip44Addresses(md5(Buffer.from('Still 21st Century')), 1)[0] !== '18EpYz5qB3XoxZWouJF3KdEp3E2nfv9FgP')
    throw new Error('Grycoin Block 1 calibration failed');
  return true;
}

module.exports = {
  ROOT, PRIZE, SUPERSEDED, EXAMPLE, md5, sha256, mnemonic, seed, master, child, derivePath, address,
  bip44Addresses, exampleParagraphs, chapterParagraphs, isLetter, toggle, flip, GROUPS, hasPrefix3c6, selftest,
};
