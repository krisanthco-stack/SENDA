'use strict';
const fs = require('fs');
const vm = require('vm');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const html = fs.readFileSync('index.html', 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert(match, 'No se encontró JavaScript inline');
let source = match[1].split("if('serviceWorker' in navigator")[0];

const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      id,
      value: '',
      innerHTML: '',
      textContent: '',
      files: [],
      options: [],
      classList: {add(){}, remove(){}, toggle(){}, contains(){return false}},
      scrollIntoView(){},
    });
  }
  return elements.get(id);
}

const storage = new Map();
// Simula un navegador que ya abrió una versión anterior: el repositorio nuevo
// debe migrar el estado local y eliminar claves FOLIO / FINCA artificiales -000.
storage.set('senda_r5_state', JSON.stringify({
  '4-200103-000': {saved:{user:'ANTERIOR'}},
  '4-108604-009': {saved:{user:'VALIDO'}}
}));
const context = {
  console,
  Date,
  Math,
  Intl,
  URL,
  Blob,
  TextDecoder: global.TextDecoder,
  TextEncoder: global.TextEncoder,
  Response: global.Response || class {},
  DecompressionStream: global.DecompressionStream || class {},
  DOMParser: class {},
  localStorage: {
    getItem(k){ return storage.has(k) ? storage.get(k) : null; },
    setItem(k,v){ storage.set(k,String(v)); },
    removeItem(k){ storage.delete(k); },
  },
  sessionStorage: {getItem(){return null}, setItem(){}},
  document: {
    getElementById(id){ return element(id); },
    createElement(){ return {click(){}, href:'', download:'', style:{}}; },
    querySelectorAll(){ return []; },
  },
  navigator: {},
  location: {protocol:'file:'},
  confirm(){ return true; },
  prompt(){ return ''; },
  setTimeout(){ return 0; },
  clearTimeout(){},
};
vm.createContext(context);
vm.runInContext(source, context);
const run = expr => vm.runInContext(expr, context);

assert(run('RELEASE_ID').includes('GITHUB-AUDITADO'), 'Release visible no corresponde a la versión auditada');
assert(run('SEED_DATA.length') === 8837, 'La base embebida debe conservar 8.837 movimientos');
assert(run("SEED_DATA.filter(r=>/-000$/.test(r.folio||'')).length") === 0, 'No puede sobrevivir un derecho artificial -000');
assert(run("formatFolio('4','200103','1')") === '4-200103-001', 'Formato FOLIO / FINCA incorrecto');
assert(run("formatFolio('4','200103','0')") === '', 'Derecho 000 no debe convertirse en folio');
assert(run("normalizeFolioValue('4-200103-001')") === '4-200103-001', 'Normalización de folio válido incorrecta');
assert(run("normalizeFolioValue('4-200103-000')") === '', 'Folio heredado -000 debe rechazarse');
assert(!run("Object.prototype.hasOwnProperty.call(state,'4-200103-000')"), 'El estado heredado -000 debe eliminarse al iniciar');
assert(run("state['4-108604-009'].saved.user") === 'VALIDO', 'La migración debe conservar estados de folios válidos');
assert(!JSON.parse(storage.get('senda_r5_state')).hasOwnProperty('4-200103-000'), 'localStorage debe reescribirse sin folios -000 heredados');

const normalized = run("normalizeRow({PROVINCIA:'4',NUMERO:'200103',DERECHO:'1',COD_DERECHO:'U',NUM_PLANO:'412345672026'},'Fincas','2026','T2',1)");
assert(normalized.folio === '4-200103-001', 'Carga nueva no forma FOLIO / FINCA correctamente');
assert(normalized.derecho === 'USUFRUCTO', 'Tipo de derecho U debe mostrarse como USUFRUCTO');
const missingRight = run("normalizeRow({PROVINCIA:'4',NUMERO:'200103',DERECHO:''},'Fincas','2026','T2',2)");
assert(missingRight.folio === '', 'Carga sin Derecho no debe inventar folio');

assert(run('pageCount(25)') === 1, 'Primera página debe contener 25');
assert(run('pageCount(26)') === 2, 'Registro 26 debe pasar a segunda página');
assert(run('pageSlice(Array.from({length:45},(_,i)=>i),2).length') === 20, 'Páginas posteriores deben contener 20');

const rights = run("[...new Map(SEED_DATA.filter(r=>/^4-108604-00[1-9]$/.test(r.folio||'')).map(r=>[r.folio,r.derecho])).entries()]");
const rightMap = new Map(rights);
for (let i=1;i<=8;i++) assert(rightMap.get(`4-108604-00${i}`) === 'NUDA PROPIEDAD', `Derecho 4-108604-00${i} debe ser NUDA PROPIEDAD`);
assert(rightMap.get('4-108604-009') === 'USUFRUCTO', 'Derecho 4-108604-009 debe ser USUFRUCTO');

// Flujo CONTROL → FINALIZADO → GESTIÓN → ELIMINAR sobre un solo folio.
for (const id of ['gFolio','gMonth','gCed','gName','gUser','gRegMonth','folioDetail']) element(id).value='';
run("actor=()=> 'AUDITOR'; observation=()=> 'VERIFICADO'; renderAll=()=>{}; toast=()=>{};");
run("finishFolio('4-108604-009')");
assert(run("state['4-108604-009'].finalized.user") === 'AUDITOR', 'FINALIZADO debe registrar usuario');
assert(run("gestionRows().some(r=>r.folio==='4-108604-009')"), 'FINALIZADO debe enviar sólo el folio a GESTIÓN');
run("deleteFolio('4-108604-009')");
assert(run("state['4-108604-009'].deleted.user") === 'AUDITOR', 'ELIMINAR FOLIO debe auditar usuario');
assert(!run("gestionRows().some(r=>r.folio==='4-108604-009')"), 'ELIMINAR FOLIO debe retirarlo de GESTIÓN sin borrar datos fuente');
assert(run("SEED_DATA.some(r=>r.folio==='4-108604-009')"), 'ELIMINAR FOLIO no debe borrar la fuente');

console.log('JS_LOGIC_AUDIT=PASS');
