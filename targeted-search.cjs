'use strict';
// Deterministic, resumable local search of two documented hypotheses.
// Usage: node quizchain-investigation/targeted-search.cjs passphrase
//        node quizchain-investigation/targeted-search.cjs groups
// Use --restart to repeat a completed or interrupted run from the beginning.
const fs=require('fs'), path=require('path'), crypto=require('crypto');
const {derivationFromBytes, TARGETS, selftest}=require('./verifier.cjs');
selftest();
const dir=__dirname, p=JSON.parse(fs.readFileSync(path.join(dir,'wattpad-paragraphs.json'),'utf8'));
const groups=[[4,5,6,7],[92,93,94,95],[167,168,169,170],[230,231,232,234]];
const mode=process.argv[2];
if (!['passphrase','groups'].includes(mode)) throw Error('Choose passphrase or groups');
const stateFile=path.join(dir,`search-${mode}-state.json`);
const resultFile=path.join(dir,`search-${mode}-results.json`);
const hitFile=path.join(dir,`search-${mode}-hits.jsonl`);
if (process.argv.includes('--restart')) {
  for (const f of [stateFile,resultFile,hitFile]) if(fs.existsSync(f)) fs.unlinkSync(f);
}
const passphrases=[
  'Second','second','SECOND','Second Life','second life','The Satoshi Code',
  'Aoi','AOI','Aoi Nakamoto','AoiNakamoto','Artificial Omnipotent Intelligence',
  'Thomas','Tom','TOMI','tomi','Satoshi','Satoshi Nakamoto','Hal','Hal Finney',
  'STNM','stnm','I STNM','FFWW','ffww','I am Satoshi','I Am Satoshi',
  'Grycoin','grycoin','Bitcoin','bitcoin','brain wallet','Brain Wallet',
  '777','777 mbtc','0.777','7','77','76','2020','2022','Tanabata',
  '14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W',
  '1EFojcAo2vbhRGCGCa7q8Wwvzss28mhQYC',
];
function flip(s) {
  const c=Array.from(s),a=c.findIndex(x=>/[A-Za-z]/.test(x)),z=c.findLastIndex(x=>/[A-Za-z]/.test(x));
  if(a<0)return s;
  c[a]=c[a].toLowerCase();c[z]=c[z].toUpperCase();return c.join('');
}
function* bases() {
  const spans=mode==='passphrase'
    ? [['all',0,p.length],['no-title',1,p.length],['story-body',3,p.length],
       ['section-I',3,87],['section-II',89,162],['section-III',164,p.length],['satoshi-code',174,246]]
    : [['groups',0,p.length]];
  const seen=new Set();
  for(const [name,start,end] of spans) {
    const masks=mode==='passphrase'?[0,1,2,4,7,8,15,16]:Array.from({length:16},(_,i)=>i);
    const subsets=mode==='passphrase'?[15]:Array.from({length:15},(_,i)=>i+1);
    for(const subset of subsets)for(const mask of masks)for(const sep of ['\n\n','\r\n\r\n'])for(const trail of ['',sep.slice(0,sep.length/2)])for(const nbsp of [false,true]) {
      const lines=[];
      for(let i=start;i<end;i++) {
        if(mode==='groups' && !groups.some((g,gid)=>(subset&(1<<gid))&&g.includes(i)))continue;
        let s=p[i]; if(nbsp)s=s.replace(/\u00a0/g,' ');
        const change=mask===16
          ? !'ITASM'.includes((s.match(/[A-Za-z]/)||[''])[0])
          : groups.some((g,gid)=>(mask&(1<<gid))&&g.includes(i));
        if(change)s=flip(s);
        lines.push(s);
      }
      const text=lines.join(sep)+trail;
      const md5=crypto.createHash('md5').update(text,'utf8').digest('hex');
      if(seen.has(md5))continue;seen.add(md5);
      yield {text,md5,label:{name,subset,mask,sep:JSON.stringify(sep),trail:JSON.stringify(trail),nbsp}};
    }
  }
}
const candidates=[];
for(const b of bases()) {
  if(mode==='passphrase')for(const passphrase of passphrases)candidates.push({...b,passphrase});
  else candidates.push(b);
}
let state=fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile,'utf8')):{next:0,checked:0,hits:0};
if(state.next>candidates.length)throw Error('Checkpoint exceeds candidate count');
for(let i=state.next;i<candidates.length;i++) {
  const {text,md5,label,passphrase}=candidates[i];
  const first=derivationFromBytes(Buffer.from(text,'utf8'),7,passphrase||'');
  state.checked+=7;
  for(const child of first.children) {
    if(TARGETS.has(child.address)) {
      fs.appendFileSync(hitFile,JSON.stringify({mode:'direct',i,md5,label,passphrase,index:child.index,child,text})+'\n');state.hits++;
    }
    if(mode==='groups') {
      const second=derivationFromBytes(Buffer.from(child.wif,'utf8'),7);
      state.checked+=7;
      for(const grandchild of second.children)if(TARGETS.has(grandchild.address)) {
        fs.appendFileSync(hitFile,JSON.stringify({mode:'nested-wif',i,md5,label,firstIndex:child.index,firstWif:child.wif,secondIndex:grandchild.index,grandchild,text})+'\n');state.hits++;
      }
    }
  }
  state.next=i+1;
  if(state.next%250===0) {
    fs.writeFileSync(stateFile,JSON.stringify(state));
    console.log(`progress ${state.next}/${candidates.length}, ${state.checked} addresses, hits=${state.hits}`);
  }
}
fs.writeFileSync(stateFile,JSON.stringify(state));
const result={mode,candidates:candidates.length,passphrases:mode==='passphrase'?passphrases.length:undefined,addressesChecked:state.checked,hits:state.hits,completed:state.next===candidates.length};
fs.writeFileSync(resultFile,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
