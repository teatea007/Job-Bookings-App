const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:844},colorScheme:'dark'});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.route(/fonts|chart/i,r=>r.abort());
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(500);
await p.evaluate(async()=>{
  await store.saveClient({id:'c1',name:'Acme Events',email:'a@b.co',contact:'Thandi'});
  await store.saveClient({id:'c2',name:'Cape Sound Co',email:'x@y.co'});
  const st=['heavy','confirmed','completed','blocked','notdone','cancelled'];
  for(let i=0;i<6;i++)await store.saveJob({id:'j'+i,title:['FOH engineer','Monitor tech','Lighting op','Hold – festival','Corporate AV','Wedding PA'][i],clientId:i%2?'c2':'c1',engineer:'Sam Lee',status:st[i],start:addDays(today(),i*2-3),items:[{desc:'Day rate',qty:1+i%3,unit:'day',rate:3500}],gst:true,payments:[],invoice:i==2?{no:'INV-1001',issued:today(),due:addDays(today(),-1)}:null});
});
await p.screenshot({path:process.argv[3]+'/home.png'});
await p.click('[data-act=tab][data-v=jobs]');await p.screenshot({path:process.argv[3]+'/jobs.png'});
await p.click('[data-act=tab][data-v=cal]');await p.screenshot({path:process.argv[3]+'/cal.png'});
await b.close()})();
