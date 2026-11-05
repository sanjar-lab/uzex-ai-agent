PAGE = r"""<!doctype html>
<html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UZEX AI-agent</title><link rel="icon" href="/logo.png">
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#14181f;--mut:#667085;--acc:#0b6bcb;--bd:#e3e6ea;--code:#f1f3f6}
@media (prefers-color-scheme:dark){:root{--bg:#0f1216;--card:#171b21;--fg:#e8eaed;--mut:#98a2b3;--acc:#4ea1ff;--bd:#2a3038;--code:#1f252d}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:860px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:8px 0 2px}.sub{color:var(--mut);margin:0 0 14px;font-size:13px}
#log{display:flex;flex-direction:column;gap:12px;margin-bottom:110px}
.m{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px 14px;white-space:pre-wrap;word-wrap:break-word}
.q{align-self:flex-end;background:var(--acc);color:#fff;border:0;max-width:85%}
details{margin-top:8px;font-size:13px;color:var(--mut)}pre{background:var(--code);padding:8px;border-radius:8px;overflow:auto;white-space:pre-wrap;font-size:12px}
.meta{font-size:12px;color:var(--mut);margin-top:6px}
form{position:fixed;left:0;right:0;bottom:0;background:var(--bg);border-top:1px solid var(--bd);padding:12px 16px}
.row{max-width:860px;margin:0 auto;display:flex;gap:8px}
textarea{flex:1;resize:none;height:52px;border:1px solid var(--bd);border-radius:10px;padding:10px;font:inherit;background:var(--card);color:var(--fg)}
button{border:0;border-radius:10px;padding:0 18px;background:var(--acc);color:#fff;font-weight:600;cursor:pointer}
button:disabled{opacity:.5}.ex{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.ex span{border:1px solid var(--bd);border-radius:999px;padding:4px 10px;font-size:13px;cursor:pointer;background:var(--card)}
</style></head><body><div class="wrap">
<h1 style="display:flex;align-items:center;gap:10px"><img src="/logo.png" alt="" width="36" height="36" style="border-radius:9px">UZEX AI-agent · birja bitimlari</h1>
<p class="sub">Javoblar faqat reyestr maʼlumotlari asosida (500 000 bitim, 2022–2026). Ответы строго по данным реестра. Har bir javob ostida SQL asosi koʻrsatiladi.</p>
<div class="ex" id="ex"></div>
<div id="log"></div></div>
<form id="f"><div class="row"><textarea id="t" placeholder="Savol bering… / Задайте вопрос…"></textarea><button id="b">➤</button></div></form>
<script>
const ex=["2025-yilda eng koʻp bitim tuzgan sotuvchi kim?","Какая общая сумма сделок по карбамиду в 2024 году?","Qaysi viloyatda eksport bitimlari eng koʻp?","Сколько сделок было аннулировано в 2026 году?"];
const exEl=document.getElementById('ex');ex.forEach(s=>{const e=document.createElement('span');e.textContent=s;e.onclick=()=>{t.value=s;send()};exEl.appendChild(e)});
const log=document.getElementById('log'),t=document.getElementById('t'),b=document.getElementById('b');let hist=[];
function add(cls,txt){const d=document.createElement('div');d.className='m '+cls;d.textContent=txt;log.appendChild(d);d.scrollIntoView({behavior:'smooth'});return d}
async function send(){const q=t.value.trim();if(!q)return;t.value='';add('q',q);const a=add('a','⏳ …');b.disabled=true;
try{const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,history:hist})});const j=await r.json();
a.textContent=j.answer||j.error;if(j.ok)hist=[...hist,{q,a:j.answer}].slice(-2);
const m=document.createElement('div');m.className='meta';m.textContent=`${j.seconds}s · ${j.provider||''}`;a.appendChild(m);
if(j.queries&&j.queries.length){const d=document.createElement('details');const s=document.createElement('summary');s.textContent=`🔎 Asos / Основание: ${j.queries.length} query`;d.appendChild(s);
j.queries.forEach(x=>{const p=document.createElement('pre');p.textContent=x.sql+'\n→ '+x.rows+' rows';d.appendChild(p)});a.appendChild(d)}}
catch(e){a.textContent='Error: '+e}b.disabled=false;t.focus()}
document.getElementById('f').onsubmit=e=>{e.preventDefault();send()};
t.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
</script></body></html>"""
