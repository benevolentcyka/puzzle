'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const L=require('../../followup-2026-09-25/lib.cjs');
const V=require('../../verifier.cjs');
const start=Date.now();
V.selftest(); L.selftest();
const historical=fs.readFileSync(path.join(__dirname,'../verification/iancoleman-2019-index.js'),'utf8');
assert(historical.includes('sjcl.hash.sha256.hash(entropy.cleanStr)'));
assert(historical.includes('var numberOfBits = 32 * mnemonicLength / 3;'));
const P=L.exampleParagraphs(); assert.equal(P.length,10);
const stream=crypto.createHash('sha256'),survivorStream=crypto.createHash('sha256');
let tested=0,survivors=0,addresses=0,hits=0;
const joins=[];
for(const sep of ['\n\n','\r\n\r\n']) {
 const base=Buffer.from(P.join(sep),'latin1'),positions=[];let off=0,local=0;
 for(const p of P){positions.push(off+[...p].findIndex(L.isLetter),off+[...p].findLastIndex(L.isLetter));off+=p.length+sep.length;}
 assert.equal(positions.length,20);
 // Gray code updates precisely one boundary letter each step.
 let previous=0;
 for(let step=0;step<2**20;step++){
  const mask=step^(step>>>1);
  if(step){let changed=mask^previous;const bit=31-Math.clz32(changed);base[positions[bit]]^=32;}
  previous=mask;tested++;
  // Length framing makes the ordered byte stream unambiguous.
  const length=Buffer.alloc(4);length.writeUInt32BE(base.length);stream.update(length).update(base);
  const md=L.md5(base);if(!L.hasPrefix3c6(md))continue;
  survivors++;local++;survivorStream.update(Buffer.from(JSON.stringify({sep,mask,md5:md.toString('hex')})+'\n'));
  const variants=[['raw',md]];
  for(const casing of ['lower','upper']){
   const hex=casing==='lower'?md.toString('hex'):md.toString('hex').toUpperCase();
   const digest=L.sha256(Buffer.from(hex,'ascii'));
   for(const bytes of [16,20,24,28,32])variants.push([`${casing}-${bytes}`,digest.subarray(0,bytes)]);
  }
  for(const [mode,entropy] of variants){
   const derived=L.bip44Addresses(entropy,21);addresses+=derived.length;
   const index=derived.indexOf(L.EXAMPLE);
   if(index>=0){hits++;fs.writeFileSync(path.join(__dirname,`FOUND-coleman-example-${hits}.json`),JSON.stringify({sep,mask,mode,index,md5:md.toString('hex'),entropy:entropy.toString('hex'),text:base.toString('latin1')},null,2));}
  }
 }
 joins.push({sep,texts:2**20,survivors:local});console.log(JSON.stringify(joins.at(-1)));
}
assert.equal(survivors,518);
const result={selftests:['author WIF vector','StageOne address','GrycoinBlock1 address'],historicalSourceSha256:L.sha256(Buffer.from(historical)).toString('hex'),questionSha256:L.sha256(Buffer.from(P.join('\n\n'),'latin1')).toString('hex'),enumeration:'Gray code over20paragraph first/last ASCIIletter toggles; joins LF LF and CRLF CRLF; no trailing newline',prefix:'3c6',modes:'rawMD5 plus SHA256(ASCIIlower/upperMD5hex) truncated16/20/24/28/32bytes',path:"m/44'/0'/0'/0/0..20",passphrase:'',encoding:'latin1 (question ASCII)',target:L.EXAMPLE,tested,survivors,entropyVariants:survivors*11,addresses,hits,joins,candidateStreamSha256:stream.digest('hex'),survivorStreamSha256:survivorStream.digest('hex'),elapsedSeconds:(Date.now()-start)/1000};
fs.writeFileSync(path.join(__dirname,'coleman-example-results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
