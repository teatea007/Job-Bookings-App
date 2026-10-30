"""Builds the AppDeploy frontend (src/app.js, src/styles.css) from the Claude Artifact version (../index.html).

The artifact keeps its data in Claude's storage and talks to Google Calendar and Gmail through
Claude connectors. Here those parts are swapped for the AppDeploy backend (/api/*), a calendar
subscription feed, .ics downloads, and the device share sheet / mail app.

Run from the repository root:  python3 appdeploy/tools/port.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = (ROOT / 'index.html').read_text()
OUT = ROOT / 'appdeploy'


def between(s, a, b):
    i = s.index(a)
    return s[i:s.index(b, i)]


def rep(s, a, b, count=1):
    n = s.count(a)
    assert n == count, (n, a[:80])
    return s.replace(a, b)


def cut(s, a, b, new):
    i = s.index(a)
    k = s.index(b, i)
    return s[:i] + new + s[k:]


# ---------- styles ----------
css = between(SRC, '<style>\n/* v2 layout', '</style>').replace('<style>\n', '', 1)
css += '''
/* sign-in screen */
.signin{min-height:calc(100vh - 140px);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:16px;padding:24px 8px}
.signin .mark{width:84px;height:84px;border-radius:24px;display:grid;place-items:center;background:linear-gradient(135deg,#0BA39C,#0B7F7A);color:#fff;font:800 28px var(--f-display);box-shadow:0 12px 30px rgba(11,127,122,.3)}
.signin h1{margin:6px 0 0;font:800 30px/1.15 var(--f-display)}
.signin p{margin:0;max-width:320px;color:var(--ink-2);font-size:16px}
.signin .btn{min-width:220px;margin-top:8px}
.signin .hint{max-width:300px}
.calurl{font:400 13px var(--f-mono);word-break:break-all;background:var(--tint);border:1px solid var(--line);border-radius:12px;padding:10px 12px;color:var(--ink-2)}
'''

# ---------- script ----------
js = between(SRC, '<script>\n"use strict";', '</script>').replace('<script>\n"use strict";\n', '', 1)

HEADER = """import { api, auth } from '@appdeploy/client';
import { Chart, registerables } from 'chart.js';
import { jsPDF } from 'jspdf';

// The app code below was written against globals; expose the bundled libraries the same way.
Chart.register(...registerables);
window.Chart = Chart;
window.jspdf = { jsPDF };

"""

DATA_LAYER = r"""/* ---------- data layer ---------- */
function withRegion(d){const s={...DEFAULTS,...d};if(!d.region){s.currency='ZAR';s.gstRate=15;s.region='ZA';s.timeZone=s.timeZone||'Africa/Johannesburg'}return s}
function upsertLocal(arr,obj){const i=arr.findIndex(x=>x.id===obj.id);if(i>=0)arr[i]=obj;else arr.push(obj)}
function sortClients(){S.clients.sort((a,b)=>(a.name||'').localeCompare(b.name||''))}
const httpStatus=e=>e?.response?.status??e?.status;
function apiErr(e){
  const st=httpStatus(e);
  if(st===401){toast('You have been signed out. Sign in again.',1);closeSheet();S.mode='signin';render()}
  else if(st===429)toast('Too many changes at once. Wait a minute and try again.',1);
  else if(st===413)toast('That record is too large to save.',1);
  else toast('Could not save. Check your connection and try again.',1);
  throw e;
}
const store={
  async saveJob(j){j.updatedAt=Date.now();const x=clone(j);try{await api.put('/api/jobs/'+encodeURIComponent(x.id),x)}catch(e){apiErr(e)}upsertLocal(S.jobs,x);sortJobs();render()},
  async deleteJob(id){try{await api.delete('/api/jobs/'+encodeURIComponent(id))}catch(e){apiErr(e)}S.jobs=S.jobs.filter(j=>j.id!==id);render()},
  async saveClient(c){c.updatedAt=Date.now();const x=clone(c);try{await api.put('/api/clients/'+encodeURIComponent(x.id),x)}catch(e){apiErr(e)}upsertLocal(S.clients,x);sortClients();render()},
  async deleteClient(id){try{await api.delete('/api/clients/'+encodeURIComponent(id))}catch(e){apiErr(e)}S.clients=S.clients.filter(c=>c.id!==id);render()},
  async saveSettings(s){const next={...S.settings,...s};try{await api.put('/api/settings',next)}catch(e){apiErr(e)}S.settings=next;render()}
};
function sortJobs(){S.jobs.sort((a,b)=>(a.start||'').localeCompare(b.start||'')||(a.callTime||'').localeCompare(b.callTime||''))}
async function loadAll(kind){
  const out=[];let next=null;
  for(let i=0;i<40;i++){const r=await api.get(`/api/${kind}`+(next?`?next=${encodeURIComponent(next)}`:''));out.push(...(r.data?.items||[]));next=r.data?.next;if(!next)break}
  return out;
}
async function loadData(){
  const [st,clients,jobs]=await Promise.all([api.get('/api/settings'),loadAll('clients'),loadAll('jobs')]);
  const saved=st.data?.settings;
  S.settings=withRegion(saved||{});
  if(!saved){if(S.user?.name&&!S.settings.ownerName)S.settings.ownerName=S.user.name;if(S.user?.email&&!S.settings.email)S.settings.email=S.user.email}
  S.clients=clients;sortClients();S.jobs=jobs;sortJobs();
}
async function boot(){
  const now=new Date();S.calMonth=iso(new Date(now.getFullYear(),now.getMonth(),1));S.calSel=today();
  renderTabs();render();
  let user=null;try{user=await auth.getUser()}catch(e){console.warn(e)}
  if(!user){S.mode='signin';render();return}
  S.user=user;
  try{await loadData();S.mode='live';S.loaded=true}catch(e){console.error(e);S.mode=httpStatus(e)===401?'signin':'error'}
  render();
}
const signInView=()=>`<div class="signin"><span class="mark">360</span><h1>My Booking 360</h1><p>Bookings, quotes, invoices and payments for engineers and techs, in one place.</p><button class="btn primary" data-act="signIn">Sign in</button><span class="hint">Use Google, Apple or a one-time email link. Your bookings are private to your account.</span></div>`;

"""

CALENDAR = r"""/* ---------- calendar (.ics) ---------- */
// Kept in step with backend/ics.ts, which serves the subscription feed.
const ICS_LABELS={blocked:'Blocked off',heavy:'Heavy pencil',confirmed:'Confirmed',completed:'Completed',notdone:'Not completed',cancelled:'Cancelled'};
const icsText=v=>String(v??'').replace(/\\/g,'\\\\').replace(/\r?\n/g,'\\n').replace(/([,;])/g,'\\$1');
function icsFold(line){const enc=new TextEncoder();let out='',cur='',n=0;for(const ch of line){const b=enc.encode(ch).length;if(n+b>74){out+=cur+'\r\n ';cur='';n=1}cur+=ch;n+=b}return out+cur}
function icsEvent(j,c,tz,stamp){
  const start=String(j.start||'');if(!/^\d{4}-\d{2}-\d{2}$/.test(start))return [];
  const end=/^\d{4}-\d{2}-\d{2}$/.test(String(j.end||''))&&j.end>start?String(j.end):start;
  const status=j.status||'heavy',label=ICS_LABELS[status]||status;
  const call=/^\d{2}:\d{2}$/.test(String(j.callTime||''))?j.callTime:'';
  const L=['BEGIN:VEVENT',`UID:${j.id}@mybooking360`,`DTSTAMP:${stamp}`];
  if(call){
    let fin=/^\d{2}:\d{2}$/.test(String(j.finishTime||''))?j.finishTime:'';
    if(!fin){const [h,m]=call.split(':').map(Number);fin=`${String(Math.min(23,h+1)).padStart(2,'0')}:${String(m).padStart(2,'0')}`}
    let ed=end;if(ed===start&&fin<=call)ed=addDays(ed,1);
    L.push(`DTSTART;TZID=${tz}:${start.replace(/-/g,'')}T${call.replace(':','')}00`,`DTEND;TZID=${tz}:${ed.replace(/-/g,'')}T${fin.replace(':','')}00`);
  }else L.push(`DTSTART;VALUE=DATE:${start.replace(/-/g,'')}`,`DTEND;VALUE=DATE:${addDays(end,1).replace(/-/g,'')}`);
  const summary=(status==='confirmed'?'':`[${label}] `)+(j.title||'Booking')+(j.engineer?` — ${j.engineer}`:'');
  const desc=[`Status: ${label}`,c&&`Client: ${c.name}`,j.engineer&&`Engineer / tech: ${j.engineer}${j.role?` (${j.role})`:''}`,j.siteContact&&`On-site: ${j.siteContact} ${j.sitePhone||''}`.trim(),j.po&&`PO / ref: ${j.po}`,j.notes&&`\n${j.notes}`,'\nManaged in My Booking 360'].filter(Boolean).join('\n');
  const loc=[j.venue,j.address].filter(Boolean).join(', ');
  L.push(`SUMMARY:${icsText(summary)}`,`DESCRIPTION:${icsText(desc)}`);if(loc)L.push(`LOCATION:${icsText(loc)}`);
  L.push(`STATUS:${status==='cancelled'?'CANCELLED':['heavy','blocked'].includes(status)?'TENTATIVE':'CONFIRMED'}`,`TRANSP:${['cancelled','notdone'].includes(status)?'TRANSPARENT':'OPAQUE'}`,'END:VEVENT');
  return L;
}
function buildIcs(jobs,timeZone){
  const tz=/^[A-Za-z_]+(\/[A-Za-z0-9_+-]+)+$/.test(timeZone||'')?timeZone:'Africa/Johannesburg';
  const stamp=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}/,'');
  const L=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//My Booking 360//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH'];
  jobs.forEach(j=>L.push(...icsEvent(j,client(j.clientId),tz,stamp)));
  L.push('END:VCALENDAR');
  return L.map(icsFold).join('\r\n')+'\r\n';
}
function addToCalendar(j){
  if(!j)return;
  const name=`${String(j.title||'booking').replace(/[^\w\- ]+/g,'').trim()||'booking'}.ics`;
  downloadBlob(name,new Blob([buildIcs([j],S.settings.timeZone)],{type:'text/calendar'}));
  toast('Calendar file saved. Open it to add the booking.');
}
const feedUrl=()=>S.settings.calToken?`${location.origin}/api/cal/${S.settings.calToken}.ics`:'';
function openCalSettings(){
  const u=feedUrl(),s=S.settings;
  openSheet('settings',head('Calendar & sync')+`<div class="sheet-body">
    <div class="card"><h3>See bookings in your phone's calendar</h3>
      <span class="hint">Subscribe once and every booking, with its status, shows in the Calendar app on your iPhone, Mac or Google Calendar. Changes appear within an hour or so.</span>
      ${u?`<div class="field"><span>Your private calendar link</span><div class="calurl">${esc(u)}</div></div>
        <div class="row"><a class="btn primary" href="${esc(u.replace(/^https?:/,'webcal:'))}">Subscribe on this device</a><button class="btn" data-act="copy" data-t="${esc(u)}">Copy link</button></div>
        <span class="hint">Google Calendar: Other calendars → From URL, then paste the link. Keep it private: anyone with the link can see your bookings.</span>
        <button class="link danger" style="align-self:flex-start" data-act="calLink">Reset link</button>`
      :`<button class="btn primary" data-act="calLink">Create my calendar link</button>`}
    </div>
    <form class="form" id="settingsForm" data-form="settings"><label class="field"><span>Calendar time zone</span><input name="timeZone" id="set-timeZone" value="${esc(s.timeZone)}"></label><button class="btn primary" type="submit">Save</button></form>
    <div class="card"><h3>One booking at a time</h3><span class="hint">Open a booking, tap ••• and choose “Add to calendar” to save it as a calendar file.</span></div>
  </div>`);
}

/* ---------- backup ---------- */
function exportBackup(){
  const data={app:'my-booking-360',version:2,exportedAt:new Date().toISOString(),settings:S.settings,clients:S.clients,jobs:S.jobs};
  downloadBlob(`my-booking-360-backup-${today()}.json`,new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
}
async function importBackup(file){
  if(!file)return;
  let d;try{d=JSON.parse(await file.text())}catch{toast('That file is not a My Booking 360 backup.',1);return}
  const clean=a=>(Array.isArray(a)?a:[]).filter(x=>x&&typeof x==='object'&&typeof x.id==='string').map(x=>{const y={...x};delete y.example;delete y._new;return y});
  const C=clean(d.clients).filter(c=>c.name),J=clean(d.jobs).filter(j=>j.title);
  if(!C.length&&!J.length&&!d.settings){toast('No bookings or clients found in that file.',1);return}
  if(!confirm(`Import ${C.length} clients and ${J.length} bookings? Records that are already here are updated, not duplicated.`))return;
  toast('Importing…');
  try{
    for(let i=0;i<C.length;i+=50)await api.post('/api/import',{clients:C.slice(i,i+50)});
    for(let i=0;i<J.length;i+=25)await api.post('/api/import',{jobs:J.slice(i,i+25)});
    if(d.settings&&typeof d.settings==='object'){const s={...d.settings};delete s.calToken;await api.put('/api/settings',{...S.settings,...s})}
    await loadData();closeSheet();render();toast(`Imported ${C.length} clients and ${J.length} bookings`);
  }catch(e){console.error(e);toast('The import stopped part way. Try again: nothing will be duplicated.',1)}
}

"""

SEND = r"""function docPdf(j,kind){return {name:invFileName(j,kind),blob:buildPdf(j,kind).output('blob')}}
async function markDocSent(j,fm,to){
  const fresh=clone(S.jobs.find(x=>x.id===j.id)),rem=!!fm.dataset.rem;
  if(fm.dataset.kind==='quote'){fresh.quote.sentAt=Date.now();fresh.quote.sentTo=to}
  else if(rem){fresh.invoice.reminders=[...(fresh.invoice.reminders||[]),Date.now()]}
  else{fresh.invoice.sentAt=Date.now();fresh.invoice.sentTo=to}
  await store.saveJob(fresh);
}
"""

js = HEADER + js
js = cut(js, '/* ---------- data layer ---------- */', '/* ---------- icons ---------- */', DATA_LAYER)
js = cut(js, '/* ---------- connectors ---------- */', '/* invoice pdf */', CALENDAR)
js = cut(js, 'function emailPayload(j,fm){', 'async function busy(', SEND)
js = cut(js, 'async function saveFile(filename,data){', '\n/* ---------- actions ---------- */',
         "function downloadBlob(filename,data){const blob=data instanceof Blob?data:new Blob([data],{type:filename.endsWith('.csv')?'text/csv':'text/plain'});const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),5000)}\nasync function saveFile(filename,data){downloadBlob(filename,data)}\n")

# render(): sign-in and error screens, tab bar only when signed in
js = rep(js, "  const v=$('#view');\n  if(S.mode==='loading')",
         "  const v=$('#view');\n  $('.tabs').hidden=S.mode!=='live';\n"
         "  if(S.mode==='signin'){v.innerHTML=signInView();return}\n"
         "  if(S.mode==='error'){v.innerHTML=`<div class=\"empty\"><b>Could not load your bookings</b><span>Check your connection and try again.</span><button class=\"btn primary\" data-act=\"reload\">Try again</button></div>`;return}\n"
         "  if(S.mode==='loading')")

# connectors are gone: everything that waited on them is always available now
js = rep(js, "${S.mcp?'':'disabled'}", '', count=js.count("${S.mcp?'':'disabled'}"))
js = rep(js, """${S.mcp?'data-send="1"':''}""", 'data-send="1"')
js = rep(js, "${S.mcp?'Generate & send':'Create invoice'}", 'Generate & send')
js = rep(js, "calSync:!!(s.autoSync&&S.mcp)", 'calSync:false')
js = re.sub(r'\n    <label class="switch"><span>Keep on Google Calendar.*?</label>', '', js, count=1, flags=re.S)
js = rep(js, "d.calSync=$('#jf-calSync').checked;", '')
js = rep(js, ";if(j.calEventId&&S.mcp)doSync(j,true)}", '}')
js = rep(js, ";if(up&&j.calEventId&&S.mcp)doSync(j,true)}", '}')
js = rep(js, "if(d.send&&S.mcp&&window.jspdf)", 'if(d.send&&window.jspdf)')
js = rep(js, "    if(job.calSync&&S.mcp)doSync(job,true);\n    else if(!job.calSync&&job.calEventId){}\n", '')
js = re.sub(r"    if\(j\.calEventId&&S\.mcp\)\{try\{await S\.mcp\.callTool\('Google Calendar','delete_event'.*?\n", '', js, count=1)
js = rep(js, "  syncCal:async(d,b)=>{const j=S.jobs.find(x=>x.id===d.id);await busy(b,()=>doSync(j))},",
         "  syncCal:d=>addToCalendar(S.jobs.find(x=>x.id===d.id)),")
js = cut(js, '  emailDraft:async(d,b)=>{', '  showPay:',
         """  mailtoDoc:async d=>{const fm=$('#emailForm');if(!fm.reportValidity())return;const j=S.jobs.find(x=>x.id===d.id),k=fm.dataset.kind||'invoice',{name,blob}=docPdf(j,k);
    const to=fm.elements.to.value.trim(),cc=fm.elements.cc.value.trim();
    downloadBlob(name,blob);
    const q=[`subject=${encodeURIComponent(fm.elements.subject.value.trim())}`,`body=${encodeURIComponent(`${fm.elements.body.value}\\n\\n[Attach ${name}]`)}`];if(cc)q.unshift(`cc=${encodeURIComponent(cc)}`);
    window.location.href=`mailto:${to}?${q.join('&')}`;
    await markDocSent(j,fm,to);toast('PDF saved. Attach it to the email that opened.')},
  signIn:async(d,b)=>{b.disabled=true;try{await auth.signInWithRedirect()}catch(e){b.disabled=false;toast(e?.code==='auth/storage-unavailable'?'Turn on website data for this site in your browser settings, then try again.':'Could not open sign-in. Try again.',1)}},
  signOut:async()=>{try{await auth.signOut()}catch{}location.reload()},
  reload:()=>location.reload(),
  exportBackup:()=>exportBackup(),
  calLink:async(d,b)=>{if(S.settings.calToken&&!confirm('Reset the link? Calendars using the old link stop updating.'))return;
    await busy(b,async()=>{try{const r=await api.post('/api/cal-token');S.settings={...S.settings,calToken:r.data.token};openCalSettings();toast('Calendar link ready')}catch(e){apiErr(e)}})},
""")

# booking sheet: calendar wording
js = re.sub(r"  const calLine=j\.calEventId\?.*?'Not on your calendar'\);\n", lambda m: "  const calLine=S.settings.calToken?'On your subscribed calendar. Changes show up automatically.':'Save it as a calendar file, or subscribe to all bookings in Settings.';\n", js, count=1, flags=re.S)
assert 'calEventId?`On Google' not in js
js = rep(js, "${ic('sync')}${j.calEventId?'Update Google Calendar':'Add to Google Calendar'}", "${ic('date')}Add to calendar")
js = rep(js, "${j.calEventId?', and the event is removed from Google Calendar':''}", '')
js = rep(js, "<b>Google Calendar</b>", "<b>Calendar</b>")
js = rep(js, "${j.calEventId?'Update':'Add'}</button>", "Add</button>")

# settings
js = rep(js, "${row('cal','sync','Calendar & sync',s.autoSync?'On':'Off')}", "${row('cal','sync','Calendar & sync',s.calToken?'Subscribed':'')}")
js = rep(js, "${row('privacy','shield','Data & privacy')}", "${row('privacy','shield','Account & backup')}")
js = cut(js, "  if(k==='privacy'){openSheet(", "  const g=GROUPS[k];",
         """  if(k==='cal'){openCalSettings();return}
  if(k==='privacy'){openSheet('settings',head('Account & backup')+`<div class="sheet-body">
    <div class="card"><dl class="kv"><dt>Signed in as</dt><dd>${esc(S.user?.email||S.user?.name||'—')}</dd><dt>Saving</dt><dd>Saved to your private My Booking 360 account, on every device you sign in on.</dd></dl></div>
    <div class="card"><h3>Backup</h3><span class="hint">Download everything as one file, or import a backup, including one from the Claude version of this app.</span>
      <div class="row"><button class="btn" data-act="exportBackup">Download backup</button><label class="btn">Import backup<input type="file" id="importFile" accept=".json,application/json" hidden></label></div></div>
    <button class="btn danger" data-act="signOut">Sign out</button></div>`);return}
""")
js = rep(js, "  if(t.dataset.actChange==='invDate'", "  if(t.id==='importFile'){importBackup(t.files[0]);t.value='';return}\n  if(t.dataset.actChange==='invDate'")

# email sheet: share sheet or mail app instead of Gmail
js = rep(js, "Sends from your Gmail.</span>", "“Share PDF” opens your phone's share sheet (Mail, Gmail, WhatsApp) with the PDF attached. “Email app” starts an email to the client and saves the PDF for you to attach.</span>")
js = rep(js, '<button class="btn" data-act="emailDraft" data-id="${j.id}">Save to Gmail drafts</button><button class="btn primary" type="submit" form="emailForm" id="sendBtn">Send now</button>',
         '<button class="btn" data-act="mailtoDoc" data-id="${j.id}">Email app</button><button class="btn primary" type="submit" form="emailForm" id="sendBtn">Share PDF</button>')
js = cut(js, "  }else if(kind==='email'){", "  }}catch(err){console.error(err)}",
         """  }else if(kind==='email'){
    const j=S.jobs.find(x=>x.id===fm.dataset.id),k=fm.dataset.kind||'invoice',{name,blob}=docPdf(j,k);
    const to=fm.elements.to.value.trim(),subject=fm.elements.subject.value.trim(),body=fm.elements.body.value;
    let file=null;try{file=new File([blob],name,{type:'application/pdf'})}catch{}
    if(!(file&&navigator.canShare&&navigator.canShare({files:[file]}))){toast('Sharing is not available on this device. Use “Email app” instead.',1);return}
    try{await navigator.share({files:[file],title:subject,text:body})}catch(err){if(err?.name!=='AbortError')toast('Sharing did not work here. Use “Email app” instead.',1);return}
    await markDocSent(j,fm,to);toast(`${k==='quote'?'Quote':'Invoice'} shared`);openJob(j.id);
""")

leftover = [w for w in ('S.mcp', 'S.dl', 'callTool', 'doSync', 'Gmail draft', 'Add to Google Calendar', 'localStorage', 'window.claude', 'S.db') if w in js]
assert not leftover, leftover

(OUT / 'src').mkdir(parents=True, exist_ok=True)
(OUT / 'src' / 'app.js').write_text(js)
(OUT / 'src' / 'styles.css').write_text(css)
print('app.js', len(js), 'styles.css', len(css))
