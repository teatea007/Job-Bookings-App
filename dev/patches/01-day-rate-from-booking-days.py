import sys
p=sys.argv[1];s=open(p).read()
E=[
("const daysBetween=(a,b)=>Math.round((pd(b)-pd(a))/864e5);",
 "const daysBetween=(a,b)=>Math.round((pd(b)-pd(a))/864e5);\nconst bookDays=d=>d.start?Math.max(1,daysBetween(d.start,d.end&&d.end>d.start?d.end:d.start)+1):1;"),
("items:s.defaultRate>0?[{desc:'Day rate',qty:1,unit:s.defaultUnit||'day',rate:+s.defaultRate}]:[]",
 "items:s.defaultRate>0?[{desc:'Day rate',qty:1,unit:s.defaultUnit||'day',rate:+s.defaultRate,auto:(s.defaultUnit||'day')==='day'}]:[]"),
("  S.draft=clone(j);const d=S.draft;\n",
 "  S.draft=clone(j);const d=S.draft;\n  const nd=bookDays(d);(d.items||[]).forEach(i=>{if(i.unit==='day'&&i.auto===undefined)i.auto=(+i.qty===nd)});\n"),
('<div class="items" id="items"></div>','<div class="items" id="items"></div><div id="dayHint"></div>'),
("Add your day rate, overtime, travel or expenses.</span>';\n  renderDraftTotals();\n}",
 """Add your day rate, overtime, travel or expenses.</span>';
  renderDayHint();renderDraftTotals();
}
function renderDayHint(){
  const d=S.draft,el=$('#dayHint');if(!el||!d)return;
  const nd=bookDays(d),days=(d.items||[]).filter(i=>i.unit==='day'),n=`${nd} booking ${nd===1?'day':'days'}`;
  el.innerHTML=!days.length?'':days.every(i=>i.auto)?`<span class="hint">Day rate × ${n}, counted from the start and end dates. Type a different quantity to override.</span>`
    :`<span class="hint">Day-rate quantity set by hand.<button type="button" class="copy" data-act="matchDays">Match ${n}</button></span>`;
}
function syncDayQty(force){
  const d=S.draft;if(!d)return;const nd=bookDays(d);
  (d.items||[]).forEach(i=>{if(i.unit==='day'&&(force||i.auto)){i.qty=nd;i.auto=true}});
  renderItems();
}"""),
("addItem:d=>{S.draft.items=S.draft.items||[];S.draft.items.push({desc:d.d||'',qty:1,unit:d.u||'day',rate:d.r?+d.r:''});",
 "addItem:d=>{S.draft.items=S.draft.items||[];const u=d.u||'day',auto=u==='day';S.draft.items.push({desc:d.d||'',qty:auto?bookDays(S.draft):1,unit:u,rate:d.r?+d.r:'',auto});"),
("  rmItem:d=>{S.draft.items.splice(+d.n,1);renderItems()},",
 "  rmItem:d=>{S.draft.items.splice(+d.n,1);renderItems()},\n  matchDays:()=>syncDayQty(true),"),
("it[t.dataset.item]=t.dataset.item==='desc'||t.dataset.item==='unit'?t.value:(t.value===''?'':+t.value);",
 "it[t.dataset.item]=t.dataset.item==='desc'||t.dataset.item==='unit'?t.value:(t.value===''?'':+t.value);\n    if(t.dataset.item==='qty')it.auto=false;\n    if(t.dataset.item==='unit'){it.auto=t.value==='day';if(it.auto){it.qty=bookDays(S.draft);row.querySelector('[data-item=qty]').value=it.qty}}\n    renderDayHint();"),
("['start','end','engineer'].includes(t.name)){S.draft[t.name]=t.value;checkClash()}",
 "['start','end','engineer'].includes(t.name)){S.draft[t.name]=t.value;checkClash();if(t.name!=='engineer')syncDayQty()}"),
]
for a,b in E:
    assert s.count(a)==1,a[:60]
    s=s.replace(a,b)
open(p,'w').write(s);print('ok')
