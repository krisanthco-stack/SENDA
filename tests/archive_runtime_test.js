'use strict';
const fs = require('fs');
const vm = require('vm');
function assert(c,m){if(!c)throw new Error(m)}
const html=fs.readFileSync('index.html','utf8');
const match=html.match(/<script>([\s\S]*?)<\/script>/); assert(match,'inline js missing');
const source=match[1].split("if('serviceWorker' in navigator")[0];
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{id,value:'',innerHTML:'',textContent:'',files:[],options:[],disabled:false,classList:{add(){},remove(){},toggle(){},contains(){return false}},scrollIntoView(){}});return elements.get(id)}
const context={console,Date,Math,Intl,URL,Blob,File:global.File,TextDecoder:global.TextDecoder,TextEncoder:global.TextEncoder,Response:global.Response,DecompressionStream:global.DecompressionStream,localStorage:{getItem(){return null},setItem(){},removeItem(){}},sessionStorage:{getItem(){return null},setItem(){}},document:{getElementById(id){return element(id)},createElement(){return {click(){},style:{}}},querySelectorAll(){return[]}},navigator:{},location:{protocol:'file:'},confirm(){return true},prompt(){return''},alert(){},setTimeout(){return 0},clearTimeout(){}};
vm.createContext(context); vm.runInContext(source,context);
(async()=>{
  const zipBuf=fs.readFileSync('/tmp/senda_archive_test/corte_test.zip');
  context.zipFile=new File([zipBuf],'corte_test.zip');
  const entries=await vm.runInContext('unzipEntries(zipFile)',context);
  assert(entries.some(e=>e.name==='Fincas_SARAPIQUI_TEST.xls'),'ZIP real no extrajo archivo interno');
  const text=new TextDecoder().decode(entries.find(e=>e.name==='Fincas_SARAPIQUI_TEST.xls').data);
  assert(text.includes('200103'),'ZIP real perdió contenido');
  vm.runInContext("sevenZipEntries=async()=>[{name:'Fincas_RAR_TEST.xls',data:new TextEncoder().encode('PROVINCIA\\tNUMERO\\tDERECHO\\tCOD_DERECHO\\tCOD_OPERACION\\tFECHA_ULT_ACT\\n4\\t200103\\t1\\tU\\tIA2\\t2026-06-01\\n')}];",context);
  context.rarFile=new File([new Uint8Array([0x52,0x61,0x72,0x21])],'corte_test.rar');
  const rarResult=await vm.runInContext("processFiles([rarFile],'2026','T2')",context);
  assert(rarResult.added.some(r=>r.folio==='4-200103-001'),'Ruta RAR no integra datos al modelo FOLIO / FINCA');
  console.log('ARCHIVE_RUNTIME_AUDIT=PASS');
})().catch(e=>{console.error(e);process.exit(1)});
