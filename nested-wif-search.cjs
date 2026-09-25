'use strict';
// Tests the two-stage WIF chain demonstrated by a solved Quizchain block:
// MD5(chapter variant) -> BIP39/BIP44 key -> WIF -> MD5(WIF) -> BIP39/BIP44 address.
// This is a targeted experiment, not an exhaustive search of chapter edits.
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');
const {derivationFromBytes, TARGETS, selftest} = require('./verifier.cjs');
selftest();
const p = JSON.parse(fs.readFileSync(path.join(__dirname, 'wattpad-paragraphs.json'), 'utf8'));
const groups = [
  [4,5,6,7], [92,93,94,95], [167,168,169,170], [230,231,232,234],
];
const selected = [
  ['all', 0, p.length], ['no-title', 1, p.length], ['story-body', 3, p.length],
  ['section-I', 3, 87], ['section-II', 89, 162], ['section-III', 164, p.length],
  ['satoshi-code', 174, 246],
];
function flip(s) {
  const chars = Array.from(s), positions = chars.flatMap((c,i) => /[A-Za-z]/.test(c) ? [i] : []);
  if (!positions.length) return s;
  chars[positions[0]] = chars[positions[0]].toLowerCase();
  chars[positions.at(-1)] = chars[positions.at(-1)].toUpperCase();
  return chars.join('');
}
let count = 0, firstStage = 0, secondStage = 0;
const seen = new Set(), hits = [];
function checkSecond(input, mode, label, firstIndex = null) {
  const d = derivationFromBytes(Buffer.from(input,'utf8'),7); secondStage++;
  for (const grandchild of d.children) {
    if (TARGETS.has(grandchild.address)) hits.push({mode,label,firstIndex,secondIndex:grandchild.index,input,grandchild});
  }
}
for (const [part, start, end] of selected) {
 for (const flipMask of [0,1,2,4,7,8,15,16]) {
  for (const separator of ['\n\n','\r\n\r\n']) {
   for (const trailing of ['', separator.slice(0,separator.length/2)]) {
    for (const nbsp of [false,true]) {
      const lines = [];
      for (let i=start; i<end; i++) {
        let s = p[i];
        if (nbsp) s=s.replace(/\u00a0/g,' ');
        if (flipMask===16 ? !'ITASM'.includes(s.match(/[A-Za-z]/)?.[0]||'')
           : groups.some((g,gid)=>(flipMask&(1<<gid)) && g.includes(i))) s=flip(s);
        lines.push(s);
      }
      const text = lines.join(separator)+trailing;
      const h = crypto.createHash('md5').update(text,'utf8').digest('hex');
      if (seen.has(h)) continue;
      seen.add(h); count++;
      const label={part,flipMask,separator:JSON.stringify(separator),trailing:JSON.stringify(trailing),nbsp,md5:h};
      const d = derivationFromBytes(Buffer.from(text,'utf8'),7); firstStage++;
      checkSecond(d.mnemonic,'nested-mnemonic',label);
      checkSecond(d.entropy,'nested-entropy-hex',label);
      for (const child of d.children) {
        if (TARGETS.has(child.address)) hits.push({mode:'direct',label,firstIndex:child.index,child});
        checkSecond(child.wif,'nested-wif',label,child.index);
        checkSecond(child.address,'nested-address',label,child.index);
        checkSecond(child.privateHex,'nested-private-hex',label,child.index);
      }
      if (count%50===0) console.log(`progress ${count} source variants, ${secondStage} second-stage inputs`);
    }
   }
  }
 }
}
const result={sourceVariants:count,firstStage,secondStage,addressesChecked:(firstStage+secondStage)*7,hits};
fs.writeFileSync(path.join(__dirname,'nested-results.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
