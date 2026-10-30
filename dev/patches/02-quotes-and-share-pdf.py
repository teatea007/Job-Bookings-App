import sys
p=sys.argv[1];s=open(p).read()
E=[
# settings defaults
("invoiceNotes:'Thank you for your business.',",
 "invoiceNotes:'Thank you for your business.',quotePrefix:'QUO-',nextQuoteNo:1001,quoteValidDays:30,"),
# settings form
("${fld('defaultRate','Default day rate','number','step=\"0.01\" min=\"0\"')}</div>",
 "${fld('defaultRate','Default day rate','number','step=\"0.01\" min=\"0\"')}</div>\n    <div class=\"grid3\">${fld('quotePrefix','Quote prefix')}${fld('nextQuoteNo','Next quote no.','number','min=\"1\"')}${fld('quoteValidDays','Quotes valid for (days)','number','min=\"1\"')}</div>"),
# job detail
("    ${invoiceBlock(j,t,ps)}\n", "    ${quoteBlock(j,t)}\n    ${invoiceBlock(j,t,ps)}\n"),
# invoice buttons
("<button class=\"btn\" data-act=\"pdfInv\" data-id=\"${j.id}\">Save PDF</button>",
 "<button class=\"btn\" data-act=\"sharePdf\" data-k=\"invoice\" data-id=\"${j.id}\">Share PDF</button>\n      <button class=\"btn\" data-act=\"pdfInv\" data-k=\"invoice\" data-id=\"${j.id}\">Save PDF</button>"),
# quote block fn
("function invoiceBlock(j,t,ps){",
 """function quoteBlock(j,t){
  const s=S.settings,q=j.quote;
  if(!q)return `<div class="card"><div class="row"><span class="spacer" style="min-width:160px"><b>Quote</b><br><small class="hint">Creates quote ${esc(s.quotePrefix)}${esc(s.nextQuoteNo)}, valid for ${esc(s.quoteValidDays)} days. Nothing is sent yet.</small></span><button class="btn sm" data-act="makeQuote" data-id="${j.id}" ${t.total>0?'':'disabled'}>Create quote</button></div>${t.total>0?'':'<span class="hint">Add charges first.</span>'}</div>`;
  const exp=q.validUntil&&q.validUntil<today()&&!q.acceptedAt;
  const pill=q.acceptedAt?'<span class="pill pp-paid">Accepted</span>':exp?'<span class="pill pp-overdue">Expired</span>':q.sentAt?'<span class="pill pp-sent">Quoted</span>':'<span class="pill pp-draft">Quote not sent</span>';
  return `<div class="card"><div class="row"><h2 class="sec spacer">Quote ${esc(q.no)}</h2>${pill}</div>
    <div class="grid2"><label class="field"><span>Quote date</span><input type="date" id="quo-issued" data-act-change="invDate" data-doc="quote" data-k="issued" data-id="${j.id}" value="${esc(q.issued)}"></label><label class="field"><span>Valid until</span><input type="date" id="quo-valid" data-act-change="invDate" data-doc="quote" data-k="validUntil" data-id="${j.id}" value="${esc(q.validUntil)}"></label></div>
    <span class="hint">${q.sentAt?`Sent ${new Date(q.sentAt).toLocaleString('en-ZA',{day:'numeric',month:'short',hour:'numeric',minute:'2-digit'})}${q.sentTo?' to '+esc(q.sentTo):''}`:'Not sent yet'}${q.acceptedAt?` · accepted ${fmtD(iso(new Date(q.acceptedAt)))}`:''} · Uses this job's current charges, ${money(t.total)}.</span>
    <div class="row">
      <button class="btn ${q.sentAt?'':'primary'}" data-act="emailQuote" data-id="${j.id}" ${S.mcp?'':'disabled'}>${q.sentAt?'Resend quote':'Email quote'}</button>
      <button class="btn" data-act="sharePdf" data-k="quote" data-id="${j.id}">Share PDF</button>
      <button class="btn" data-act="pdfInv" data-k="quote" data-id="${j.id}">Save PDF</button>
      ${q.sentAt?'':`<button class="btn" data-act="markQuoteSent" data-id="${j.id}">Mark as sent</button>`}
      ${q.acceptedAt?'':`<button class="btn" data-act="acceptQuote" data-id="${j.id}">Client accepted</button>`}
    </div></div>`;
}
function invoiceBlock(j,t,ps){"""),
# pdf
("function buildPdf(j){","function buildPdf(j,kind='invoice'){"),
("const s=S.settings,c=client(j.clientId)||{},t=totals(j),i=j.invoice,W=210,L=18,R=W-18;",
 "const Q=kind==='quote',s=S.settings,c=client(j.clientId)||{},t=totals(j),i=Q?j.quote:j.invoice,W=210,L=18,R=W-18;"),
("doc.text(s.gstRegistered?'TAX INVOICE':'INVOICE',R,y,{align:'right'});",
 "doc.text(Q?'QUOTATION':s.gstRegistered?'TAX INVOICE':'INVOICE',R,y,{align:'right'});"),
("let ry=y+7;[['Invoice no.',i.no],['Issued',fmtLong(i.issued)],['Due',fmtLong(i.due)],j.po&&['Your ref',j.po]]",
 "let ry=y+7;(Q?[['Quote no.',i.no],['Date',fmtLong(i.issued)],['Valid until',fmtLong(i.validUntil)],j.po&&['Your ref',j.po]]:[['Invoice no.',i.no],['Issued',fmtLong(i.issued)],['Due',fmtLong(i.due)],j.po&&['Your ref',j.po]])"),
("doc.text('BILL TO',L,y);","doc.text(Q?'PREPARED FOR':'BILL TO',L,y);"),
("  if(t.paid){tl('Paid',`-${cur(t.paid)}`);","  if(!Q&&t.paid){tl('Paid',`-${cur(t.paid)}`);"),
("doc.text('How to pay',L,y);","doc.text(Q?'Accepting this quote':'How to pay',L,y);"),
("  [s.accountName&&`Account name: ${s.accountName}`,",
 "  (Q?[`This quote is valid until ${fmtLong(i.validUntil)}.`,`To accept, reply to this email or contact us quoting ${i.no}.`,`Dates are held as provisional until the quote is accepted.`,`Payment terms: ${s.termsDays} days from invoice.`]:[s.accountName&&`Account name: ${s.accountName}`,"),
("`Please pay by ${fmtLong(i.due)}.`].filter(Boolean)","`Please pay by ${fmtLong(i.due)}.`]).filter(Boolean)"),
("function invFileName(j){return `${j.invoice.no} ",
 "function invFileName(j,kind){return `${(kind==='quote'?j.quote:j.invoice).no} "),
# email
("function openEmail(j){\n  const c=client(j.clientId)||{},t=totals(j),i=j.invoice,s=S.settings,rem=!!i.sentAt&&t.balance>0;",
 "function openEmail(j,kind='invoice'){\n  const Q=kind==='quote',c=client(j.clientId)||{},t=totals(j),i=Q?j.quote:j.invoice,s=S.settings,rem=!Q&&!!i.sentAt&&t.balance>0;"),
("  const msg=rem?",
 "  const msg=Q?`Hi ${c.contact||c.name||''},\\n\\nThank you for the enquiry. Please find attached quote ${i.no} for ${j.title} (${fmtRange(j.start,jobEnd(j))}).\\n\\nTotal: ${money(t.total)}${j.gst?' incl. VAT':''}\\nValid until: ${fmtLong(i.validUntil)}\\n\\nTo confirm the booking, simply reply to this email.\\n\\nKind regards,\\n${who}`\n    :rem?"),
("openSheet('email',head(rem?'Payment reminder':'Email invoice')+`<div class=\"sheet-body\"><form id=\"emailForm\" data-form=\"email\" data-id=\"${j.id}\" data-rem=\"${rem?1:''}\" class=\"card\">",
 "openSheet('email',head(Q?'Email quote':rem?'Payment reminder':'Email invoice')+`<div class=\"sheet-body\"><form id=\"emailForm\" data-form=\"email\" data-id=\"${j.id}\" data-kind=\"${kind}\" data-rem=\"${rem?1:''}\" class=\"card\">"),
("value=\"${esc(`${rem?'Reminder: ':''}Invoice ${i.no} – ${j.title}`)}\"",
 "value=\"${esc(Q?`Quote ${i.no} – ${j.title}`:`${rem?'Reminder: ':''}Invoice ${i.no} – ${j.title}`)}\""),
("<span class=\"hint\">Attached: ${esc(invFileName(j))} · ${money(t.balance)} due. Sends from your Gmail.</span>",
 "<span class=\"hint\">Attached: ${esc(invFileName(j,kind))} · ${Q?money(t.total)+' quoted':money(t.balance)+' due'}. Sends from your Gmail.</span>"),
("  const doc=buildPdf(j),b64=doc.output('datauristring').split(',')[1];",
 "  const kind=fm.dataset.kind||'invoice',doc=buildPdf(j,kind),b64=doc.output('datauristring').split(',')[1];"),
("filename:invFileName(j),mimeType","filename:invFileName(j,kind),mimeType"),
("      if(rem){fresh.invoice.reminders=[...(fresh.invoice.reminders||[]),Date.now()]}else{fresh.invoice.sentAt=Date.now();fresh.invoice.sentTo=to}\n      await store.saveJob(fresh);toast(`${rem?'Reminder':'Invoice'} sent to ${to}`);",
 "      if(fm.dataset.kind==='quote'){fresh.quote.sentAt=Date.now();fresh.quote.sentTo=to}else if(rem){fresh.invoice.reminders=[...(fresh.invoice.reminders||[]),Date.now()]}else{fresh.invoice.sentAt=Date.now();fresh.invoice.sentTo=to}\n      await store.saveJob(fresh);toast(`${fm.dataset.kind==='quote'?'Quote':rem?'Reminder':'Invoice'} sent to ${to}`);"),
# actions
("  pdfInv:async d=>{const j=S.jobs.find(x=>x.id===d.id);if(!window.jspdf){toast('The PDF maker did not load. Reload and try again.',1);return}await saveFile(invFileName(j),buildPdf(j).output('blob'))},",
 """  pdfInv:async d=>{const j=S.jobs.find(x=>x.id===d.id),k=d.k||'invoice';if(!window.jspdf){toast('The PDF maker did not load. Reload and try again.',1);return}await saveFile(invFileName(j,k),buildPdf(j,k).output('blob'))},
  sharePdf:async d=>{const j=S.jobs.find(x=>x.id===d.id),k=d.k||'invoice';if(!window.jspdf){toast('The PDF maker did not load. Reload and try again.',1);return}
    const name=invFileName(j,k),blob=buildPdf(j,k).output('blob');let file=null;try{file=new File([blob],name,{type:'application/pdf'})}catch{}
    if(file&&navigator.canShare&&navigator.canShare({files:[file]})){try{await navigator.share({files:[file],title:name.replace(/\\.pdf$/,'')});return}catch(e){if(e?.name==='AbortError')return}}
    toast('Sharing is not available here, so the PDF is being saved instead.');await saveFile(name,blob)},
  makeQuote:async(d,b)=>{const j=clone(S.jobs.find(x=>x.id===d.id)),s=S.settings,no=`${s.quotePrefix||''}${s.nextQuoteNo||1001}`;
    j.quote={no,issued:today(),validUntil:addDays(today(),+s.quoteValidDays||30),sentAt:null};
    await busy(b,async()=>{await store.saveSettings({nextQuoteNo:(+s.nextQuoteNo||1001)+1});await store.saveJob(j)});toast(`Quote ${no} created`)},
  emailQuote:d=>{const j=S.jobs.find(x=>x.id===d.id);if(!window.jspdf){toast('The PDF maker did not load. Reload and try again.',1);return}openEmail(j,'quote')},
  markQuoteSent:async d=>{const j=clone(S.jobs.find(x=>x.id===d.id));j.quote.sentAt=Date.now();await store.saveJob(j);toast('Quote marked as sent')},
  acceptQuote:async d=>{const j=clone(S.jobs.find(x=>x.id===d.id));j.quote.acceptedAt=Date.now();const up=['heavy','blocked'].includes(j.status);if(up)j.status='confirmed';
    await store.saveJob(j);toast(up?'Quote accepted. Booking confirmed.':'Quote accepted');if(up&&j.calEventId&&S.mcp)doSync(j,true)},"""),
("Object.assign(j,{id:newId(),status:'heavy',invoice:null,","Object.assign(j,{id:newId(),status:'heavy',invoice:null,quote:null,"),
(";delete j.invoice;openJobForm(j)}",";delete j.invoice;delete j.quote;openJobForm(j)}"),
("if(t.dataset.actChange==='invDate'&&t.value){const j=clone(S.jobs.find(x=>x.id===t.dataset.id));j.invoice[t.dataset.k]=t.value;await store.saveJob(j);toast('Invoice date saved')}",
 "if(t.dataset.actChange==='invDate'&&t.value){const j=clone(S.jobs.find(x=>x.id===t.dataset.id)),doc=t.dataset.doc||'invoice';j[doc][t.dataset.k]=t.value;await store.saveJob(j);toast(doc==='quote'?'Quote date saved':'Invoice date saved')}"),
("client(j.clientId)?.name,j.invoice?.no]","client(j.clientId)?.name,j.invoice?.no,j.quote?.no]"),
]
for a,b in E:
    assert s.count(a)==1,a[:70]
    s=s.replace(a,b)
open(p,'w').write(s);print('ok')
