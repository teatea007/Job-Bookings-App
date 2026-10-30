import sys,re
p=sys.argv[1];s=open(p).read()
a=s.index(':root{\n  --bg:#F2F4F8');b=s.index('\n*{box-sizing:border-box}')
new=''':root{
  /* Light tropical palette: warm ivory paper, lagoon teal accent, orchid / mango / jade / hibiscus status colours. */
  --bg:#FFF8F1; --surface:#FFFFFF; --surface-2:#FDEFE4; --line:#F1DED0;
  --ink:#2B1D30; --ink-2:#5E4C64; --ink-3:#8F7E96;
  --accent:#08807C; --accent-ink:#FFFFFF; --accent-soft:#D9F4F1;
  --st-blocked:#8A4BC2; --st-heavy:#C46A00; --st-confirmed:#178A50; --st-completed:#2667C9; --st-notdone:#D63A55; --st-cancelled:#9A8F9E;
  --good:#178A50; --warn:#C46A00; --bad:#D63A55;
  --tropic:linear-gradient(120deg,#FF6F61 0%,#FFB347 45%,#2EC4B6 100%);
  --f-display:"Archivo","Arial Narrow",system-ui,sans-serif;
  --f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --f-mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,monospace;
  --r:14px; --nav-h:64px; color-scheme:light;
}
'''
s=s[:a]+new+s[b:]
E=[
("body{background:var(--bg);color:var(--ink);",
 "body{background:radial-gradient(900px 420px at 100% -10%,#FFE3D3 0%,transparent 60%),radial-gradient(800px 420px at -10% 110%,#D6F5EF 0%,transparent 60%),var(--bg);background-attachment:fixed;color:var(--ink);"),
(".top{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:var(--surface);border-bottom:1px solid var(--line);",
 ".top{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:color-mix(in srgb,var(--surface) 88%,transparent);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);box-shadow:inset 0 -3px 0 -1px transparent;"),
(".mark{width:34px;height:34px;border-radius:9px;background:var(--ink);color:var(--surface);",
 ".top::after{content:\"\";position:absolute;left:0;right:0;bottom:-1px;height:3px;background:var(--tropic)}\n.mark{width:34px;height:34px;border-radius:10px;background:var(--tropic);color:#fff;text-shadow:0 1px 2px rgba(80,20,20,.35);box-shadow:0 2px 8px rgba(255,111,97,.35);"),
(".btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}",
 ".btn.primary{background:linear-gradient(135deg,#0BA39C,var(--accent));border-color:var(--accent);color:var(--accent-ink);box-shadow:0 2px 8px rgba(8,128,124,.25)}"),
(".stat{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:12px 14px;",
 ".stat{background:var(--surface);border:1px solid var(--line);border-top:3px solid var(--sc,var(--accent));border-radius:var(--r);padding:12px 14px;box-shadow:0 1px 3px rgba(120,60,40,.06);"),
(".stat.bad .val{color:var(--bad)}",
 ".stat.bad .val{color:var(--bad)}\n.stats>.stat:nth-child(1){--sc:#2EC4B6}.stats>.stat:nth-child(2){--sc:#FFB347}.stats>.stat:nth-child(3){--sc:#FF6F61}.stats>.stat:nth-child(4){--sc:#9B5DE5}"),
(".chip[aria-pressed=\"true\"]{background:var(--ink);border-color:var(--ink);color:var(--surface)}",
 ".chip[aria-pressed=\"true\"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}"),
(".av{width:36px;height:36px;border-radius:50%;background:var(--accent-soft);color:var(--accent);",
 ".av{width:36px;height:36px;border-radius:50%;background:var(--tropic);color:#fff;"),
(".tabs{position:fixed;left:0;right:0;bottom:0;z-index:20;background:var(--surface);",
 ".tabs{position:fixed;left:0;right:0;bottom:0;z-index:20;background:color-mix(in srgb,var(--surface) 92%,transparent);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);"),
(".tab[aria-current=\"page\"]{color:var(--accent)}",
 ".tab[aria-current=\"page\"]{color:var(--accent)}\n.tab[aria-current=\"page\"] svg{filter:drop-shadow(0 2px 4px rgba(8,128,124,.3))}"),
(".bar-row .track i{display:block;height:100%;background:var(--accent);",
 ".bar-row .track i{display:block;height:100%;background:var(--tropic);"),
(".card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);",
 ".card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);box-shadow:0 1px 3px rgba(120,60,40,.06);"),
(".job{display:grid;grid-template-columns:52px minmax(0,1fr) auto;gap:12px;align-items:center;width:100%;text-align:left;background:var(--surface);",
 ".job{display:grid;grid-template-columns:52px minmax(0,1fr) auto;gap:12px;align-items:center;width:100%;text-align:left;background:linear-gradient(90deg,color-mix(in srgb,var(--stc) 7%,var(--surface)),var(--surface) 40%);box-shadow:0 1px 3px rgba(120,60,40,.06);"),
(".sheet{position:fixed;inset:0;z-index:40;display:flex;align-items:flex-end;justify-content:center;background:rgba(10,14,22,.45)}",
 ".sheet{position:fixed;inset:0;z-index:40;display:flex;align-items:flex-end;justify-content:center;background:rgba(43,29,48,.38)}"),
("{label:'Received',data:f.rec,backgroundColor:css('--good')","{label:'Received',data:f.rec,backgroundColor:'#FFB347'"),
]
for x,y in E:
    assert s.count(x)==1,x[:60]
    s=s.replace(x,y)
open(p,'w').write(s);print('ok')
