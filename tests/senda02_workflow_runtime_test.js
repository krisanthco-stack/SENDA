'use strict';
const fs=require('fs');const h=fs.readFileSync('index.html','utf8');
function ok(c,m){if(!c)throw new Error(m)}
for(const x of ['function selectReviewFolio','function finishReviewFolio','function returnFolioToSenda','function gestionBaseRows','controlSelectedFolio','control-accordion','CÉDULAS JURÍDICAS','BASE GESTIÓN JSON','BASE GESTIÓN EXCEL'])ok(h.includes(x),x);
ok(h.includes('senda02_data')&&h.includes('senda02_state')&&h.includes('senda02_catalog'),'storage keys are not isolated');
ok(!h.includes("const DATA_KEY='senda_r5_data'"),'legacy data key leaked');
console.log('SENDA02_WORKFLOW=PASS');
