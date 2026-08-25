'use strict';
const fs=require('fs'),vm=require('vm');
function assert(c,m){if(!c)throw new Error(m)}
const html=fs.readFileSync('index.html','utf8');
const match=html.match(/<script>([\s\S]*?)<\/script>/);assert(match,'inline JS missing');
const source=match[1].split("if('serviceWorker' in navigator")[0];
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{id,value:'',innerHTML:'',textContent:'',files:[],options:[],disabled:false,className:'',dataset:{},classList:{add(){},remove(){},toggle(){},contains(){return false}},scrollIntoView(){}});return elements.get(id)}
const storage=new Map();
// R6 state exists in same browser; SENDA 02 must ignore it.
storage.set('senda_r5_state',JSON.stringify({'4-108604-009':{finalized:{user:'R6'}}}));
const context={console,Date,Math,Intl,URL,Blob,TextDecoder:global.TextDecoder,TextEncoder:global.TextEncoder,Response:global.Response||class{},DecompressionStream:global.DecompressionStream||class{},DOMParser:class{},localStorage:{getItem(k){return storage.get(k)||null},setItem(k,v){storage.set(k,String(v))},removeItem(k){storage.delete(k)}},sessionStorage:{getItem(){return null},setItem(){}},document:{getElementById:id=>element(id),createElement(){return {click(){},href:'',download:'',style:{}}},querySelectorAll(){return[]}},navigator:{},location:{protocol:'file:'},confirm(){return true},prompt(){return''},alert(){},setTimeout(){return 0},clearTimeout(){}};
vm.createContext(context);vm.runInContext(source,context);const run=e=>vm.runInContext(e,context);
assert(run('RELEASE_ID')==='SENDA-02-2026.08.25-R2-CONTROL','release incorrect');
assert(run('DATA_KEY')==='senda02_data','SENDA 02 must have isolated data key');
assert(run('STATE_KEY')==='senda02_state','SENDA 02 must have isolated state key');
assert(run('SEED_DATA.length')===8837,'base must retain 8837 movements');
assert(!run("Object.prototype.hasOwnProperty.call(state,'4-108604-009')"),'R6 state leaked into SENDA 02');
assert(run("formatFolio('4','200103','1')")==='4-200103-001','folio format');
assert(run("formatFolio('4','200103','0')")==='','000 must be rejected');
assert(run('pageCount(25)')===1,'page 25');assert(run('pageCount(26)')===2,'page 26');assert(run('pageSlice(Array.from({length:45},(_,i)=>i),2).length')===20,'subsequent page 20');
const rights=run("[...new Map(SEED_DATA.filter(r=>/^4-108604-00[1-9]$/.test(r.folio||'')).map(r=>[r.folio,r.derecho])).entries()]");const m=new Map(rights);for(let i=1;i<=8;i++)assert(m.get(`4-108604-00${i}`)==='NUDA PROPIEDAD','nuda '+i);assert(m.get('4-108604-009')==='USUFRUCTO','usufructo');
for(const id of ['gFolio','gMonth','gCed','gName','gUser','gRegMonth','folioDetail','controlList','cFolio','cMonth','cCed','cName','cPlano','cType'])element(id).value='';
run("actor=()=> 'AUDITOR 02'; observation=()=> 'REVISADO'; renderAll=()=>{}; toast=()=>{};");
run("finishReviewFolio('4-108604-009')");
assert(run("state['4-108604-009'].finalized.user")==='AUDITOR 02','finalized user');
assert(run("gestionRows().some(r=>r.folio==='4-108604-009')"),'must enter gestion');
run("confirm=()=>true; returnFolioToSenda('4-108604-009')");
assert(!run("!!state['4-108604-009'].finalized"),'return must remove finalized');
assert(!run("gestionRows().some(r=>r.folio==='4-108604-009')"),'returned folio must leave gestion');
console.log('SENDA02_JS_LOGIC=PASS');
