'use strict';
// Summarize actual result records; an assumed negative is never a completed run.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const patterns=[/^example-unfiltered-.*\.json$/,/^example-edit-.*\.json$/,/^example-converter-prefix-errors\d\.json$/,/^language-settings-.*\.json$/,/^example-encoding-errors\d\.json$/,/^chapter-whitespace-indices.*\.json$/,/^chapter-nbsp-indices.*\.json$/];
const records=[];
for(const name of fs.readdirSync(__dirname).sort()){
 if(name.includes('.invalid.')||!patterns.some(p=>p.test(name)))continue;
 const bytes=fs.readFileSync(path.join(__dirname,name)),r=JSON.parse(bytes);
 assert.equal(typeof r.complete,'boolean',name);assert.equal(r.matches,0,`Inspect potential match: ${name}`);
 const indices=r.indices??[r.index];assert(indices.every(Number.isInteger),name);
 const addressOperations=r.derived_addresses??r.next_rank*indices.length;
 assert.equal(addressOperations,r.next_rank*indices.length,name);
 assert(r.next_rank<=r.candidates_total,name);assert.equal(r.complete,r.next_rank===r.candidates_total,name);
 records.push({file:name,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),complete:r.complete,
  source_operations:r.enumerated_texts??null,entropy_candidates_total:r.candidates_total,
  checked_entropy_candidates:r.next_rank,indices,derived_address_operations:addressOperations,
  matches:r.matches,gpu_kernel_sha256:r.gpu_kernel_sha256});
}
assert(new Set(records.map(r=>r.gpu_kernel_sha256)).size===1,'Mixed repaired GPU kernel fingerprints');
const out={updated_utc:new Date().toISOString(),status:'unsolved',pair_family_assumption:'Treat negative only for choosing follow-up work; do not mark an incomplete or invalid run complete.',
 count_note:'Operations overlap between families; these totals are not unique addresses or a proof of exhaustion.',
 complete_records:records.filter(r=>r.complete).length,incomplete_records:records.filter(r=>!r.complete).length,
 completed_address_operations:records.filter(r=>r.complete).reduce((n,r)=>n+r.derived_address_operations,0),
 incomplete_address_operations:records.filter(r=>!r.complete).reduce((n,r)=>n+r.derived_address_operations,0),records};
fs.writeFileSync(path.join(__dirname,'post-pair-ledger.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({complete_records:out.complete_records,incomplete_records:out.incomplete_records,completed_address_operations:out.completed_address_operations,incomplete_address_operations:out.incomplete_address_operations,status:out.status}));
