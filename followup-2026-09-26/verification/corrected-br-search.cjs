'use strict';
// Independent serialization: promote LF breaks before converting newline bytes once.
const fs = require('fs'), path = require('path'), assert = require('assert');
const L = require('../../followup-2026-09-25/lib.cjs');
const V = require('../../verifier.cjs');
const paras = L.chapterParagraphs();
const br = paras.flatMap((p,i) => p.includes('\n') ? [i] : []);
assert.equal(br.length, 10);
assert(paras.every(p => !p.includes('\r')));
const g123 = [...L.GROUPS.g1,...L.GROUPS.g2,...L.GROUPS.g3];
const groups = {raw:[], g123, g1234:[...g123,...L.GROUPS.g4]};
function build(group, nbsp, newline, mask) {
  const set = new Set(group);
  let s = paras.map((p,i) => {
    let q = set.has(i) ? L.flip(p) : p;
    if (nbsp === 'sp') q = q.replace(/\u00a0/g,' ');
    const k = br.indexOf(i);
    return k >= 0 && (mask & (1 << k)) ? q.replace(/\n/g,'\n\n') : q;
  }).join('\n\n');
  if (newline === 'CRLF') s = s.replace(/\n/g,'\r\n');
  assert(!s.includes('\r\r\n'));
  if (newline === 'CRLF') assert(!s.replace(/\r\n/g,'').match(/[\r\n]/));
  else assert(!s.includes('\r'));
  return s;
}
const authorEntropy = Buffer.from('2941774a2abec9f30c7d6777d1d53d91','hex');
const stageEntropy = Buffer.from('9dd2efb9bc976c2095bd534d7b8d431c','hex');
const author = V.derivationFromEntropy(authorEntropy,2);
assert.equal(author.children[1].wif,'L5Z66qPmUkTAsWQywjRNHDxHrX6J1X1SQedp6V8QsbaXR7rGd6ex');
const stage = V.derivationFromEntropy(stageEntropy,1);
assert.equal(stage.children[0].address,'19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN');
for (const e of [authorEntropy,stageEntropy]) {
  assert.deepEqual(L.bip44Addresses(e,2),V.derivationFromEntropy(e,2).children.map(c=>c.address));
  assert.equal(L.mnemonic(e),V.mnemonic(e));
}
const result = {scope:'all 1024 internal-break subsets; MD5 raw entropy; empty passphrase; BIP44 external account zero indices 0-20',sourceJsonSha256:L.sha256(fs.readFileSync(path.join(L.ROOT,'wattpad-paragraphs.json'))).toString('hex'),brParagraphIndices:br,byteAssertions:'no CRCRLF; CRLF contains no bare CR/LF; source has LF only',calibration:{author:{entropy:author.entropy,mnemonic:author.mnemonic,addresses:author.children.map(c=>c.address),wifIndexOneVerified:true},stageOne:{entropy:stage.entropy,mnemonic:stage.mnemonic,address:stage.children[0].address},independentImplementationsAgree:true},families:[],hits:[],texts:0,addressComparisons:0};
const started=Date.now();
for (const [name,group] of Object.entries(groups)) for (const nbsp of ['keep','sp']) for (const newline of ['LF','CRLF']) {
  const row = {group:name,nbsp,newline,texts:0,addresses:0,firstMd5:null,lastMd5:null};
  for (let mask=0;mask<1024;mask++) {
    const text=build(group,nbsp,newline,mask), entropy=L.md5(Buffer.from(text,'utf8'));
    if (!mask) row.firstMd5=entropy.toString('hex');
    row.lastMd5=entropy.toString('hex');
    const addresses=L.bip44Addresses(entropy,21);
    addresses.forEach((address,index)=>{ if(V.TARGETS.has(address)) result.hits.push({group:name,nbsp,newline,mask,index,address,entropy:entropy.toString('hex')}); });
    row.texts++; row.addresses+=addresses.length;
  }
  result.families.push(row); result.texts+=row.texts; result.addressComparisons+=row.addresses;
  fs.writeFileSync(path.join(__dirname,'corrected-br-results.json'),JSON.stringify({...result,elapsedSeconds:(Date.now()-started)/1000,complete:false},null,2)+'\n');
  console.log(JSON.stringify(row));
}
result.elapsedSeconds=(Date.now()-started)/1000; result.complete=true;
fs.writeFileSync(path.join(__dirname,'corrected-br-results.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({texts:result.texts,addressComparisons:result.addressComparisons,hits:result.hits,elapsedSeconds:result.elapsedSeconds}));
