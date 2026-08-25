'use strict';
const fs=require('fs'),vm=require('vm');
function assert(c,m){if(!c)throw new Error(m)}
const html=fs.readFileSync('index.html','utf8');
assert(html.includes('DESELECCIONAR'),'CONTROL must expose DESELECCIONAR');
const match=html.match(/<script>([\s\S]*?)<\/script>/);assert(match,'inline JS missing');
const source=match[1].split("if('serviceWorker' in navigator")[0];
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{id,value:'',innerHTML:'',textContent:'',files:[],options:[],disabled:false,className:'',dataset:{},classList:{add(){},remove(){},toggle(){},contains(){return false}},scrollIntoView(){}});return elements.get(id)}
const storage=new Map();
const context={console,Date,Math,Intl,URL,Blob,TextDecoder:global.TextDecoder,TextEncoder:global.TextEncoder,Response:global.Response||class{},DecompressionStream:global.DecompressionStream||class{},DOMParser:class{},localStorage:{getItem(k){return storage.get(k)||null},setItem(k,v){storage.set(k,String(v))},removeItem(k){storage.delete(k)}},sessionStorage:{getItem(){return null},setItem(){}},document:{getElementById:id=>element(id),createElement(){return {click(){},href:'',download:'',style:{}}},querySelectorAll(){return[]}},navigator:{},location:{protocol:'file:'},confirm(){return true},prompt(){return''},alert(){},setTimeout(){return 0},clearTimeout(){}};
vm.createContext(context);vm.runInContext(source,context);const run=e=>vm.runInContext(e,context);
for(const id of ['gFolio','gMonth','gCed','gName','gUser','gRegMonth','folioDetail','controlList','cFolio','cMonth','cCed','cName','cPlano','cType'])element(id).value='';
run("renderControl=()=>{}; renderDashboard=()=>{}; toast=()=>{}; showSection=()=>{}; selectReviewFolio('4-108604-009')");
assert(run("controlSelectedFolio")==='4-108604-009', 'selection from INFORMACIÓN SENDA must centralize in CONTROL');
assert(run("state['4-108604-009'].review.selected")===true, 'selection state must be active');
run("deselectControlFolio()");
assert(run("controlSelectedFolio")==='', 'deselect must clear only control selection');
assert(!run("!!state['4-108604-009']?.finalized"),'deselect must not finalize');
assert(!run("gestionRows().some(r=>r.folio==='4-108604-009')"),'deselect must not move folio to gestion');
run("actor=()=> 'AUDITOR 02'; observation=()=> 'FINALIZADO'; renderAll=()=>{}; toast=()=>{}; finishReviewFolio('4-108604-009')");
assert(run("!!state['4-108604-009'].finalized"),'finalize must set finalized');
assert(run("gestionRows().some(r=>r.folio==='4-108604-009')"),'finalize must move folio to gestion');
console.log('SENDA02_CONTROL_DESELECT=PASS');
