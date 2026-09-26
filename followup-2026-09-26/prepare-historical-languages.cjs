'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const commit='45e40c288fe0d6cfba2c57a68f421eeb34d41385';
const languages=['english','japanese','spanish','chinese_simplified','chinese_traditional','french','italian','korean'];
const dir=path.join(__dirname,'verification','languages');fs.mkdirSync(dir,{recursive:true});
async function get(url){const r=await fetch(url);if(!r.ok)throw Error(`${r.status}: ${url}`);return Buffer.from(await r.arrayBuffer());}
(async()=>{
 const results=await Promise.allSettled(languages.map(async language=>{
  const url=`https://raw.githubusercontent.com/iancoleman/bip39/${commit}/src/js/wordlist_${language}.js`;
  const bytes=await get(url);const match=bytes.toString('utf8').match(/WORDLISTS\["[a-z_]+"\]\s*=\s*(\[[\s\S]*\])\s*;?\s*$/);
  assert(match,`Unexpected wordlist format: ${language}`);const words=JSON.parse(match[1]);assert.equal(words.length,2048);assert.equal(new Set(words).size,2048);
  const sha256=crypto.createHash('sha256').update(bytes).digest('hex');
  fs.writeFileSync(path.join(dir,`${language}.json`),JSON.stringify({language,commit,url,sha256,words},null,2)+'\n');
  return{language,words:words.length,sha256};
 }));
 for(const r of results)console.log(r.status==='fulfilled'?JSON.stringify(r.value):String(r.reason));
 if(results.some(r=>r.status==='rejected'))throw Error('One or more historical wordlists failed');
 const url='https://raw.githubusercontent.com/trezor/python-mnemonic/master/vectors.json';const bytes=await get(url);
 fs.writeFileSync(path.join(dir,'trezor-vectors.json'),bytes);console.log(JSON.stringify({vectorsSource:url,sha256:crypto.createHash('sha256').update(bytes).digest('hex')}));
})();
