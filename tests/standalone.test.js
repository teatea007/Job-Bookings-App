// End-to-end check of the GitHub Pages build against a fake Google (sign-in, Drive, Calendar, Gmail).
// Run from the repo root: node tests/standalone.test.js
const {chromium}=require('playwright');const http=require('http');const fs=require('fs');const path=require('path');
const ROOT=path.resolve(__dirname,'..'),PORT=8765,BASE=`http://localhost:${PORT}/Job-Bookings-App/`;
const types={'.html':'text/html','.js':'text/javascript','.json':'application/json','.webmanifest':'application/manifest+json','.png':'image/png'};
const server=http.createServer((q,r)=>{let f=decodeURIComponent(q.url.split('?')[0].replace('/Job-Bookings-App',''));if(f.endsWith('/'))f+='index.html';
  fs.readFile(path.join(ROOT,f),(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'});r.end(d)})});
const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)process.exitCode=1};
(async()=>{await new Promise(r=>server.listen(PORT,r));
const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:844}});
p.on('pageerror',e=>ok(false,'page error: '+e.message));
const g={drive:null,driveTime:0,events:[],mails:[],auth:[]};
await p.route(/fonts\.g/,r=>r.abort());
await p.route(/Chart\.js/,r=>r.abort());
await p.route(/jspdf/,r=>r.fulfill({path:require.resolve('jspdf/dist/jspdf.umd.min.js'),contentType:'text/javascript'}));
await p.route('**/config.js',r=>r.fulfill({contentType:'text/javascript',body:"window.MB360_CONFIG={googleClientId:'test.apps.googleusercontent.com'};"}));
await p.route(u=>u.hostname==='accounts.google.com',r=>{const u=new URL(r.request().url()),q=u.searchParams;g.auth.push(q.get('prompt')||'interactive');
  r.fulfill({status:302,headers:{location:`${q.get('redirect_uri')}#access_token=tok${g.auth.length}&token_type=Bearer&expires_in=3599&state=${q.get('state')}`}})});
await p.route(u=>/(^|\.)googleapis\.com$/.test(u.hostname),async r=>{const q=r.request(),u=new URL(q.url()),m=q.method();
  const json=(o,s=200)=>r.fulfill({status:s,contentType:'application/json',body:JSON.stringify(o)});
  if(!/^Bearer tok/.test(q.headers()['authorization']||''))return json({error:{message:'no token'}},401);
  if(u.pathname==='/drive/v3/files')return json({files:g.drive?[{id:'f1',modifiedTime:String(g.driveTime)}]:[]});
  if(u.pathname==='/drive/v3/files/f1'&&u.searchParams.get('alt')==='media')return json(g.drive);
  if(u.pathname.startsWith('/upload/drive/v3/files')){const body=q.postData();const parts=body.split(/--mb360[^\r\n]*/);g.drive=JSON.parse(parts[2].split('\r\n\r\n')[1]);g.driveTime++;return json({id:'f1',modifiedTime:String(g.driveTime)})}
  if(u.pathname.startsWith('/calendar/v3/calendars/primary/events')){const ev=JSON.parse(q.postData()||'{}');g.events.push({m,ev});return json({id:'ev1',...ev})}
  if(u.pathname==='/gmail/v1/users/me/profile')return json({emailAddress:'owner@example.com'});
  if(u.pathname==='/gmail/v1/users/me/messages/send'){g.mails.push(Buffer.from(JSON.parse(q.postData()).raw,'base64').toString());return json({id:'m1'})}
  return json({error:{message:'unmocked '+u.pathname}},404)});

await p.goto(BASE);await p.waitForTimeout(400);
ok(await p.isVisible('[data-act=signIn]'),'first open shows Sign in with Google');
await p.click('[data-act=signIn]');await p.waitForURL(u=>u.href.startsWith(BASE));await p.waitForTimeout(800);
ok(await p.evaluate(()=>S.mode)==='live','signed in after Google redirect');
ok(g.drive&&Array.isArray(g.drive.jobs),'created the data file in Drive');
ok(!(await p.evaluate(()=>location.hash)),'token removed from the address bar');

await p.evaluate(async()=>{await store.saveSettings({businessName:'Test Sound',defaultRate:3500});
  await store.saveClient({id:'c1',name:'Acme Events',email:'acme@example.com'});
  await store.saveJob({id:'j1',title:'FOH engineer',clientId:'c1',status:'heavy',start:'2026-11-02',end:'2026-11-04',items:[{desc:'Day rate',qty:3,unit:'day',rate:3500}],gst:true,payments:[]})});
await p.waitForTimeout(1500);
ok(g.drive.jobs.length===1&&g.drive.clients.length===1&&g.drive.settings.businessName==='Test Sound','changes saved to Drive');
ok((await p.textContent('#topSub'))==='Saved to Google Drive','header shows saved state');

await p.evaluate(()=>openJob('j1'));await p.click('[data-act=syncCal]');await p.waitForTimeout(800);
const ev=g.events[0];ok(ev&&ev.m==='POST'&&ev.ev.start.date==='2026-11-02'&&ev.ev.end.date==='2026-11-05'&&ev.ev.colorId==='5','calendar event created as all-day 2–4 Nov, heavy-pencil colour');
await p.waitForTimeout(900);ok(g.drive.jobs[0].calEventId==='ev1','calendar event id saved');
await p.click('[data-act=setStatus][data-v=confirmed]');await p.waitForTimeout(900);
ok(g.events[1]&&g.events[1].m==='PATCH'&&g.events[1].ev.colorId==='10','status change updated the calendar event');

await p.click('[data-act=makeQuote]');await p.waitForTimeout(500);await p.click('[data-act=emailQuote]');await p.click('#sendBtn');await p.waitForTimeout(1000);
const mail=g.mails[0]||'';ok(/To: acme@example.com/.test(mail)&&/application\/pdf; name="QUO-1001 Acme Events.pdf"/.test(mail),'quote emailed through Gmail with the PDF attached');
await p.waitForTimeout(900);ok(g.drive.jobs[0].quote?.sentTo==='acme@example.com','quote marked as sent');

g.drive.clients.push({id:'c2',name:'Added on another device'});g.driveTime++;
await p.reload();await p.waitForTimeout(1200);
ok(await p.evaluate(()=>S.clients.length)===2,'reopening loads the latest data from Drive');
ok(g.auth.length===1,'reopening reuses the saved sign-in');

await p.evaluate(()=>{const o=JSON.parse(localStorage.getItem('mb360-token'));o.e=Date.now()-1000;localStorage.setItem('mb360-token',JSON.stringify(o))});
await p.reload();await p.waitForURL(u=>u.href.startsWith(BASE));await p.waitForTimeout(1200);
ok(g.auth[1]==='none'&&await p.evaluate(()=>S.mode)==='live','expired sign-in renews silently');

await b.close();server.close();})();
