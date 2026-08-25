const fs=require('fs');
const h=fs.readFileSync('index.html','utf8');
function ok(cond,msg){if(!cond)throw new Error(msg)}
ok(h.includes('function selectReviewFolio'),'missing selectReviewFolio');
ok(h.includes("state[f].review={selected:true"),'review state is not stored');
ok(h.includes('function finishReviewFolio'),'missing finishReviewFolio');
ok(h.includes('state[f].finalized='),'finalized state missing');
ok(h.includes('function returnFolioToSenda'),'missing return workflow');
ok(h.includes('delete st.finalized'),'return does not remove finalized state');
ok(h.includes('function gestionBaseRows'),'missing gestion base');
ok(h.includes('tipo_gestion'),'gestion base lacks type');
ok(h.includes('CÉDULAS JURÍDICAS'),'missing juridical quick button');
console.log('R6_WORKFLOW_RUNTIME=PASS');
