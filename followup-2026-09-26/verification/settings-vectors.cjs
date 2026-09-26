'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const L=require('../../followup-2026-09-25/lib.cjs');
const commit='45e40c288fe0d6cfba2c57a68f421eeb34d41385';
const source=fs.readFileSync(path.join(__dirname,'iancoleman-2019-index.js'),'utf8');
assert(source.includes('sjcl.hash.sha256.hash(entropy.cleanStr)'));
assert(source.includes('var numberOfBits = 32 * mnemonicLength / 3;'));
const results=[];
for(const original of ['2941774a2abec9f30c7d6777d1d53d91','9dd2efb9bc976c2095bd534d7b8d431c']) for(const c of ['lower','upper']) {
 const input=c==='upper'?original.toUpperCase():original;
 const digest=crypto.createHash('sha256').update(input,'utf8').digest();
 for(const words of [12,15,18,21,24]) {
  const entropy=digest.subarray(0,words*4/3);
  results.push({original,case:c,words,asciiSha256:digest.toString('hex'),entropy:entropy.toString('hex'),mnemonic:L.mnemonic(entropy),addresses:L.bip44Addresses(entropy,2)});
 }
}
const files=['iancoleman-2019-index.js','iancoleman-2019-entropy.js','iancoleman-2019-index.html','iancoleman-2019-LICENSE'];
const document={historicalCommit:commit,sourceDate:'2019-07-18T10:50:14Z',license:'MIT; copyright (c) 2014-2016 Ian Coleman; upstream license preserved in iancoleman-2019-LICENSE',apiQuery:'https://api.github.com/repos/iancoleman/bip39/commits?path=src/js/index.js&until=2019-08-01T00:00:00Z&per_page=1',sources:files.map((file,i)=>({file,url:`https://raw.githubusercontent.com/iancoleman/bip39/${commit}/${['src/js/index.js','src/js/entropy.js','src/index.html','LICENSE'][i]}`,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,file))).digest('hex')})),results};
fs.writeFileSync(path.join(__dirname,'settings-vectors.json'),JSON.stringify(document,null,2)+'\n');
console.log(JSON.stringify({historicalCommit:commit,vectors:results.length}));
