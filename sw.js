// Offline support: the app itself is fetched fresh when online and served from cache when not.
// Google sign-in and API calls are never cached.
const CACHE='mb360-v2';
const SHELL=['./','./index.html','./config.js','./manifest.webmanifest','./icons/icon-192.png','./icons/apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
const keep=(req,res)=>{if(res.ok||res.type==='opaque'){const copy=res.clone();caches.open(CACHE).then(c=>c.put(req,copy))}return res};
self.addEventListener('fetch',e=>{
  const req=e.request,u=new URL(req.url);
  if(req.method!=='GET')return;
  if(u.origin===location.origin){e.respondWith(fetch(req).then(r=>keep(req,r)).catch(()=>caches.match(req,{ignoreSearch:true}).then(m=>m||caches.match('./'))));return}
  if(/(^|\.)cdnjs\.cloudflare\.com$|(^|\.)fonts\.(googleapis|gstatic)\.com$/.test(u.hostname))e.respondWith(caches.match(req).then(m=>m||fetch(req).then(r=>keep(req,r))));
});
