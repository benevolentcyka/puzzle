'use strict';
// Reads a local copy of Hal Finney's public bitcointalk post, then reconstructs
// the confirmed solved Quizchain stage. The post itself is not embedded here.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {derivationFromBytes} = require('./verifier.cjs');
const source = fs.readFileSync(path.join(__dirname,'hal-finney-page.html'),'latin1');
const match = /<div class="post">([\s\S]*?)<\/div>/.exec(source);
if (!match) throw new Error('Forum post not found');
const body = match[1]
  .replace(/<br\s*\/?>\s*<br\s*\/?>/gi,'\n\n')
  .replace(/<br\s*\/?>/gi,'\n')
  .replace(/<[^>]*>/g,'')
  .replace(/&#039;/g,"'").replace(/&quot;/g,'"').replace(/&amp;/g,'&').trim();
const paragraphs = body.split('\n\n');
if (paragraphs.length!==16) throw new Error(`Expected 16 paragraphs; got ${paragraphs.length}`);
const transformed = paragraphs.map(p=>{
  if ('ITASM'.includes(p[0])) return p;
  const c=Array.from(p), a=c.findIndex(x=>/[A-Za-z]/.test(x));
  const z=c.findLastIndex(x=>/[A-Za-z]/.test(x));
  c[a]=c[a].toLowerCase(); c[z]=c[z].toUpperCase();
  return c.join('');
}).join('\n\n');
const bytes=Buffer.from(transformed,'utf8');
const md5=crypto.createHash('md5').update(bytes).digest('hex');
const address=derivationFromBytes(bytes,1).children[0].address;
if (md5!=='9dd2efb9bc976c2095bd534d7b8d431c') throw new Error(`Unexpected MD5 ${md5}`);
if (address!=='19TbyN5KCg1Lg7qHwezifsLVcdSa2Rj5KN') throw new Error(`Unexpected address ${address}`);
console.log(JSON.stringify({paragraphs:paragraphs.length,md5,address,verified:true}));
