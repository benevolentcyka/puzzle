'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const repaired='9429b7fc2cd5499ceb2993d2d375b8213ca7be61a6a2c4dae0ed1dc7cf0e0cd2';
const records=[];
for(const name of fs.readdirSync(__dirname).sort()) {
 if(!/^(chapter-subsets-|historical-wallets-).*\.json$/.test(name))continue;
 const bytes=fs.readFileSync(path.join(__dirname,name)),r=JSON.parse(bytes),c=r.configuration;
 assert.equal(c.gpu_kernel_sha256,repaired,`Unreviewed GPU fingerprint: ${name}`);
 assert.equal(r.complete,r.next_rank===r.candidates_total,name);
 assert(r.next_rank>=0&&r.next_rank<=r.candidates_total,name);
 assert.equal(r.matches,0,`Inspect potential match: ${name}`);
 const perSeed=name.startsWith('historical-wallets-')?c.paths.reduce((n,p)=>n+(p.direct?1:c.indices.length),0):c.indices.length;
 assert.equal(r.derived_addresses,r.next_rank*perSeed,name);
 records.push({file:name,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),
  complete:r.complete,candidates_total:r.candidates_total,next_rank:r.next_rank,
  derived_address_operations:r.derived_addresses,matches:r.matches,configuration:c});
}
const out={updated_utc:new Date().toISOString(),status:'unsolved',
 count_note:'Address operations overlap. A complete finite family is not exhaustion of the puzzle.',
 complete_records:records.filter(r=>r.complete).length,incomplete_records:records.filter(r=>!r.complete).length,
 completed_address_operations:records.filter(r=>r.complete).reduce((n,r)=>n+r.derived_address_operations,0),
 incomplete_address_operations:records.filter(r=>!r.complete).reduce((n,r)=>n+r.derived_address_operations,0),records};
fs.writeFileSync(path.join(__dirname,'ledger.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({...out,records:undefined}));
