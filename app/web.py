PAGE = r"""<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UZEX AI-agent — birja bitimlari tahlilchisi</title>
<meta name="description" content="UZEX birja bitimlari reyestri bo'yicha savollarga faqat ma'lumotlar asosida javob beruvchi AI-agent">
<link rel="icon" href="/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#f3f7fd; --card:#ffffff; --ink:#0f172a; --ink2:#334155; --mut:#64748b; --line:#e5ecf6;
  --blue:#1d4ed8; --blue2:#2563eb; --sky:#0ea5e9; --teal:#14b8a6; --mint:#10b981; --amber:#f59e0b; --rose:#f43f5e; --violet:#8b5cf6;
  --grad:linear-gradient(135deg,#1d4ed8 0%,#0ea5e9 55%,#14b8a6 100%);
  --soft:0 1px 2px rgba(15,23,42,.04),0 8px 24px rgba(30,64,175,.07);
  --r:18px;
}
*{box-sizing:border-box}
html,body{margin:0}
body{font:15px/1.55 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg);
  background-image:radial-gradient(900px 500px at 8% -10%,rgba(14,165,233,.16),transparent 60%),
  radial-gradient(800px 480px at 100% 0%,rgba(20,184,166,.14),transparent 60%);background-attachment:fixed;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:1280px;margin:0 auto;padding:0 20px}
/* nav */
nav{position:sticky;top:0;z-index:20;backdrop-filter:saturate(1.4) blur(14px);background:rgba(243,247,253,.78);border-bottom:1px solid rgba(229,236,246,.8)}
nav .wrap{display:flex;align-items:center;gap:14px;height:66px}
.brand{display:flex;align-items:center;gap:11px;text-decoration:none}
.brand img{width:40px;height:40px;border-radius:12px;box-shadow:0 4px 14px rgba(14,165,233,.25)}
.brand b{font-size:17px;letter-spacing:-.01em}.brand small{display:block;color:var(--mut);font-size:12px;font-weight:500;margin-top:-2px}
.sp{flex:1}
.pill{display:inline-flex;align-items:center;gap:7px;padding:6px 12px;border-radius:999px;background:#fff;border:1px solid var(--line);font-size:12.5px;font-weight:600;color:var(--ink2)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--mint);box-shadow:0 0 0 4px rgba(16,185,129,.15);animation:pulse 2s infinite}
@keyframes pulse{50%{box-shadow:0 0 0 7px rgba(16,185,129,.05)}}
.seg{display:inline-flex;background:#fff;border:1px solid var(--line);border-radius:12px;padding:3px}
.seg button{border:0;background:transparent;font:600 13px Inter,sans-serif;color:var(--mut);padding:6px 11px;border-radius:9px;cursor:pointer}
.seg button.on{background:var(--grad);color:#fff}
.btn{display:inline-flex;align-items:center;gap:8px;border:0;border-radius:12px;padding:10px 16px;font:600 14px Inter,sans-serif;cursor:pointer;text-decoration:none;transition:transform .15s,box-shadow .15s}
.btn.pri{background:var(--grad);color:#fff;box-shadow:0 6px 18px rgba(37,99,235,.28)}
.btn.pri:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(37,99,235,.33)}
.btn.ghost{background:#fff;border:1px solid var(--line);color:var(--ink2)}
.btn.ghost:hover{border-color:#c9d8ee}
/* hero */
.hero{padding-top:34px;padding-bottom:8px}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:12.5px;font-weight:700;color:var(--blue2);background:rgba(37,99,235,.08);padding:6px 12px;border-radius:999px;letter-spacing:.02em}
h1{font-size:clamp(26px,3.6vw,40px);line-height:1.15;letter-spacing:-.025em;margin:14px 0 10px;font-weight:800}
h1 em{font-style:normal;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.lead{color:var(--ink2);font-size:16.5px;max-width:760px;margin:0}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:26px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:16px 16px 14px;box-shadow:var(--soft);position:relative;overflow:hidden}
.kpi:after{content:"";position:absolute;right:-30px;top:-30px;width:90px;height:90px;border-radius:50%;background:var(--c,#2563eb);opacity:.08}
.kpi .ic{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-size:17px;background:color-mix(in srgb,var(--c,#2563eb) 12%,#fff)}
.kpi .v{font-size:23px;font-weight:800;letter-spacing:-.02em;margin-top:10px;font-variant-numeric:tabular-nums}
.kpi .l{color:var(--mut);font-size:12.5px;font-weight:500}
/* main grid */
.grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:18px;margin-top:22px;margin-bottom:22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--soft)}
.card h3{margin:0;font-size:15px;font-weight:700;letter-spacing:-.01em}
.card .sub{color:var(--mut);font-size:12.5px}
/* chat */
.chat{display:flex;flex-direction:column;height:760px}
.chat-h{display:flex;align-items:center;gap:12px;padding:16px 18px;border-bottom:1px solid var(--line)}
.chat-h .av{width:38px;height:38px;border-radius:12px;background:var(--grad);display:grid;place-items:center;color:#fff;font-size:18px}
.log{flex:1;overflow:auto;padding:18px;display:flex;flex-direction:column;gap:14px;scroll-behavior:smooth}
.empty{margin:auto 0;text-align:center;padding:10px}
.empty .big{font-size:40px}
.empty h4{margin:8px 0 4px;font-size:18px}
.empty p{color:var(--mut);margin:0 0 16px}
.chips{display:grid;grid-template-columns:1fr 1fr;gap:8px;text-align:left}
.chip{border:1px solid var(--line);background:linear-gradient(#fff,#f8fbff);border-radius:14px;padding:11px 13px;cursor:pointer;font-size:13.5px;color:var(--ink2);transition:all .15s;display:flex;gap:9px;align-items:flex-start}
.chip:hover{border-color:#bcd3f3;transform:translateY(-1px);box-shadow:0 6px 16px rgba(37,99,235,.08)}
.chip span{font-size:17px;line-height:1.2}
.msg{max-width:92%;animation:in .25s ease-out}
@keyframes in{from{opacity:0;transform:translateY(6px)}}
.q{align-self:flex-end;background:var(--grad);color:#fff;padding:11px 15px;border-radius:16px 16px 4px 16px;box-shadow:0 6px 16px rgba(37,99,235,.2);white-space:pre-wrap}
.a{align-self:flex-start;background:#fff;border:1px solid var(--line);border-radius:16px 16px 16px 4px;padding:14px 16px;box-shadow:var(--soft);width:92%}
.a .txt{white-space:pre-wrap;color:var(--ink)}
.a .txt.err{color:#b45309}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px}
.tag{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;font-weight:600;padding:4px 9px;border-radius:999px;background:#f1f5fb;color:var(--ink2)}
.tag.ok{background:rgba(16,185,129,.1);color:#047857}
.tag.m{background:rgba(37,99,235,.08);color:var(--blue)}
.achart{margin-top:12px;border:1px solid var(--line);border-radius:14px;padding:10px 12px 6px;background:linear-gradient(#fbfdff,#fff)}
.achart .t{font-size:12px;color:var(--mut);font-weight:600;margin-bottom:4px}
details.basis{margin-top:10px}
details.basis summary{cursor:pointer;font-size:12.5px;font-weight:600;color:var(--blue2);list-style:none;display:inline-flex;gap:6px;align-items:center}
details.basis summary::-webkit-details-marker{display:none}
details.basis summary:before{content:"▸";transition:transform .15s}
details.basis[open] summary:before{transform:rotate(90deg)}
pre.sql{font:12px/1.5 "JetBrains Mono",ui-monospace,Consolas,monospace;background:#0f172a;color:#e2e8f0;border-radius:12px;padding:12px 14px;white-space:pre-wrap;word-break:break-word;margin:8px 0 0}
pre.sql .r{color:#5eead4}
.typing{display:flex;gap:5px;align-items:center;color:var(--mut);font-size:13px}
.typing i{width:7px;height:7px;border-radius:50%;background:var(--sky);animation:b 1.2s infinite}
.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
@keyframes b{40%{transform:translateY(-5px);opacity:.5}}
.steps-mini{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.steps-mini span{font-size:11.5px;padding:3px 8px;border-radius:8px;background:#f1f5fb;color:var(--mut)}
.steps-mini span.on{background:rgba(14,165,233,.12);color:#0369a1}
.composer{padding:14px;border-top:1px solid var(--line);display:flex;gap:10px;align-items:flex-end;background:linear-gradient(#fff,#fafcff);border-radius:0 0 var(--r) var(--r)}
.composer textarea{flex:1;resize:none;min-height:50px;max-height:140px;border:1.5px solid var(--line);border-radius:14px;padding:13px 14px;font:15px Inter,sans-serif;color:var(--ink);background:#fff;outline:none;transition:border-color .15s,box-shadow .15s}
.composer textarea:focus{border-color:#93c5fd;box-shadow:0 0 0 4px rgba(59,130,246,.12)}
.send{width:50px;height:50px;border-radius:14px;border:0;background:var(--grad);color:#fff;font-size:20px;cursor:pointer;box-shadow:0 6px 16px rgba(37,99,235,.28)}
.send:disabled{opacity:.5;cursor:wait}
/* insights */
.ins{display:flex;flex-direction:column;gap:18px}
.ch{padding:16px 18px}
.ch .hd{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:8px}
.ch canvas{width:100%!important}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
/* how */
.how{margin-top:8px;margin-bottom:26px}
.how h2{font-size:22px;letter-spacing:-.02em;margin:0 0 4px}
.steps{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-top:16px}
.step{background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:16px;box-shadow:var(--soft);position:relative}
.step .n{position:absolute;top:12px;right:14px;font-weight:800;color:#dbe7f7;font-size:26px}
.step .i{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;font-size:19px;color:#fff;background:var(--grad)}
.step b{display:block;margin:10px 0 4px}
.step p{margin:0;color:var(--mut);font-size:13px}
footer{padding:22px 0 34px;color:var(--mut);font-size:13px;border-top:1px solid var(--line)}
footer .wrap{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
.badges{display:flex;flex-wrap:wrap;gap:6px}
.badges span{background:#fff;border:1px solid var(--line);border-radius:8px;padding:4px 9px;font-weight:600;color:var(--ink2);font-size:12px}
@media (max-width:1100px){.kpis{grid-template-columns:repeat(3,1fr)}.steps{grid-template-columns:repeat(2,1fr)}}
@media (max-width:960px){.grid{grid-template-columns:1fr}.chat{height:72vh;min-height:520px}}
@media (max-width:640px){.wrap{padding:0 14px}.kpis{grid-template-columns:repeat(2,1fr)}.chips{grid-template-columns:1fr}.two{grid-template-columns:1fr}
  .steps{grid-template-columns:1fr}.hide-sm{display:none}.a,.msg{max-width:100%;width:100%}}
</style>
</head>
<body>
<nav><div class="wrap">
  <a class="brand" href="/"><img src="/logo.png" alt=""><div><b>UZEX AI-agent</b><small data-i="tag">Birja bitimlari tahlilchisi</small></div></a>
  <div class="sp"></div>
  <span class="pill hide-sm"><span class="dot"></span><span data-i="online">Onlayn</span></span>
  <div class="seg"><button data-l="uz" class="on">UZ</button><button data-l="ru">RU</button></div>
  <a class="btn pri hide-sm" href="https://t.me/XG_tech_bot" target="_blank" rel="noopener">✈️ Telegram</a>
</div></nav>

<header class="wrap hero">
  <span class="eyebrow">✦ <span data-i="eyebrow">UZEX AI Hackathon 2026 · Prototip</span></span>
  <h1 data-i="h1html"></h1>
  <p class="lead" data-i="lead"></p>
  <div class="kpis" id="kpis"></div>
</header>

<main class="wrap grid">
  <section class="card chat" id="chat">
    <div class="chat-h">
      <div class="av">✦</div>
      <div><h3 data-i="chatTitle">AI-chat</h3><div class="sub" data-i="chatSub"></div></div>
      <div class="sp"></div>
      <button class="btn ghost" id="newBtn">🆕 <span data-i="new">Yangi suhbat</span></button>
    </div>
    <div class="log" id="log"></div>
    <form class="composer" id="f">
      <textarea id="t" rows="1"></textarea>
      <button class="send" id="b" aria-label="send">➤</button>
    </form>
  </section>

  <aside class="ins">
    <div class="card ch"><div class="hd"><h3 data-i="cYear">Yillar bo'yicha savdo</h3><span class="sub" data-i="cYearS"></span></div><canvas id="cYear" height="190"></canvas></div>
    <div class="card ch"><div class="hd"><h3 data-i="cMonth">Oylik dinamika</h3><span class="sub" data-i="cMonthS"></span></div><canvas id="cMonth" height="150"></canvas></div>
    <div class="two">
      <div class="card ch"><div class="hd"><h3 data-i="cCat">Kategoriyalar</h3></div><canvas id="cCat" height="230"></canvas></div>
      <div class="card ch"><div class="hd"><h3 data-i="cReg">Top viloyatlar</h3></div><canvas id="cReg" height="230"></canvas></div>
    </div>
  </aside>
</main>

<section class="wrap how">
  <h2 data-i="howT">Qanday ishlaydi</h2>
  <div class="sub" data-i="howS"></div>
  <div class="steps" id="steps"></div>
</section>

<footer><div class="wrap">
  <div>© 2026 UZEX AI-agent · <span data-i="foot">Barcha raqamlar reyestr ma'lumotlaridan olinadi</span></div>
  <div class="badges"><span>Claude Sonnet 5.5</span><span>Gemini</span><span>Groq</span><span>DuckDB</span><span>FastAPI</span><span>Telegram</span></div>
</div></footer>

<script>
const I18N={
 uz:{tag:"Birja bitimlari tahlilchisi",online:"Onlayn",eyebrow:"UZEX AI Hackathon 2026 · Prototip",
  h1html:"Birja bitimlari haqida so'rang — <em>javob faqat ma'lumotlardan</em>",
  lead:"AI-agent savolingizni ma'lumotlar bazasiga SQL-so'rovga aylantiradi, natijani tekshiradi va aniq raqam, nom va STIR bilan javob beradi. Ma'lumotda javob bo'lmasa — buni ochiq aytadi.",
  k:["Bitimlar","Savdo hajmi","Kompaniyalar","Brokerlar","Eksport bitimlari"],
  chatTitle:"AI-chat",chatSub:"Oʻzbek (lotin/kirill) yoki rus tilida yozing",new:"Yangi suhbat",
  ph:"Savolingizni yozing… (Enter — yuborish)",emptyT:"Nimani bilmoqchisiz?",emptyP:"Namuna savollardan birini bosing yoki o'zingiz yozing",
  ex:[["🏆","2025-yilda eng koʻp bitim tuzgan sotuvchi kim?"],["🧪","Karbamid boʻyicha 2024-yildagi jami savdo summasi qancha?"],["🌍","Qaysi viloyatda eksport bitimlari eng koʻp?"],["❌","2026-yilda nechta bitim bekor qilingan?"],["💵","2025-yil 15-martdagi dollar kursi qancha boʻlgan?"],["🌱","2025-yilda eng koʻp paxta xom ashyosi sotib olgan xaridor kim?"]],
  thinking:"Ma'lumotlar tekshirilmoqda",st:["Savolni tahlil","Nomlarni topish","SQL-so'rov","Tekshiruv"],
  verified:"SQL bilan tasdiqlangan",basis:"Javob asosi",rows:"qator",chartT:"So'rov natijasi",err:"Xatolik. Iltimos, qayta urinib ko'ring.",
  cYear:"Yillar bo'yicha savdo",cYearS:"trln so'm · bitimlar soni",cMonth:"Oylik dinamika",cMonthS:"bitimlar soni",cCat:"Kategoriyalar",cReg:"Top viloyatlar",
  deals:"Bitimlar",turn:"Savdo, trln so'm",
  howT:"Qanday ishlaydi",howS:"Har bir javob 5 bosqichdan o'tadi — raqamlar hech qachon «o'ylab topilmaydi».",
  steps:[["💬","Savol","O'zbek yoki rus tilida, erkin shaklda"],["🔍","Nomlarni topish","Kompaniya, tovar, broker — kirill va lotin moslashtiriladi"],["🗄️","SQL-so'rov","500 000 bitimli DuckDB bazasida aniq hisob-kitob"],["✅","Tekshiruv","Javobdagi har bir raqam so'rov natijasi bilan solishtiriladi"],["📊","Javob + asos","Aniq javob, ishlatilgan SQL va grafik"]],
  foot:"Barcha raqamlar reyestr ma'lumotlaridan olinadi",tr:"trln so'm",bn:"mlrd"},
 ru:{tag:"Аналитик биржевых сделок",online:"Онлайн",eyebrow:"UZEX AI Hackathon 2026 · Прототип",
  h1html:"Спросите о биржевых сделках — <em>ответ строго по данным</em>",
  lead:"AI-агент превращает ваш вопрос в SQL-запрос к базе, проверяет результат и отвечает точными цифрами, названиями и ИНН. Если в данных ответа нет — честно об этом говорит.",
  k:["Сделок","Объём торгов","Компаний","Брокеров","Экспортных сделок"],
  chatTitle:"AI-чат",chatSub:"Пишите на русском или узбекском",new:"Новый диалог",
  ph:"Задайте вопрос… (Enter — отправить)",emptyT:"Что вы хотите узнать?",emptyP:"Нажмите на пример или задайте свой вопрос",
  ex:[["🏆","Кто из продавцов заключил больше всего сделок в 2025 году?"],["🧪","Какая общая сумма сделок по карбамиду в 2024 году?"],["🌍","В каком регионе больше всего экспортных сделок?"],["❌","Сколько сделок было аннулировано в 2026 году?"],["💵","Какой был курс доллара 15 марта 2025 года?"],["🌱","Кто купил больше всего хлопка-сырца в 2025 году?"]],
  thinking:"Проверяю данные",st:["Разбор вопроса","Поиск названий","SQL-запрос","Проверка"],
  verified:"Подтверждено SQL",basis:"Основание ответа",rows:"строк",chartT:"Результат запроса",err:"Ошибка. Пожалуйста, попробуйте ещё раз.",
  cYear:"Торги по годам",cYearS:"трлн сум · число сделок",cMonth:"Помесячная динамика",cMonthS:"число сделок",cCat:"Категории",cReg:"Топ регионов",
  deals:"Сделки",turn:"Торги, трлн сум",
  howT:"Как это работает",howS:"Каждый ответ проходит 5 шагов — цифры никогда не «придумываются».",
  steps:[["💬","Вопрос","На русском или узбекском, в свободной форме"],["🔍","Поиск названий","Компания, товар, брокер — кириллица и латиница сопоставляются"],["🗄️","SQL-запрос","Точный расчёт по базе DuckDB из 500 000 сделок"],["✅","Проверка","Каждое число в ответе сверяется с результатом запроса"],["📊","Ответ + основание","Точный ответ, использованный SQL и график"]],
  foot:"Все цифры берутся из данных реестра",tr:"трлн сум",bn:"млрд"}
};
const CATS_RU2UZ={"Сельскохозяйственная продукция":"Qishloq xo'jaligi","Продовольственные товары":"Oziq-ovqat","Нефтепродукты":"Neft mahsulotlari","Строительные материалы":"Qurilish materiallari","Полимерная продукция":"Polimerlar","Химическая продукция":"Kimyo","Металлопродукция":"Metall","Промышленные товары":"Sanoat tovarlari"};
const PAL=["#2563eb","#14b8a6","#0ea5e9","#8b5cf6","#10b981","#f59e0b","#f43f5e","#6366f1"];
let L="uz";try{L=localStorage.getItem("uzex_lang")||"uz"}catch(e){}
let hist=[],STATS=null,charts={};
const $=s=>document.querySelector(s),log=$("#log"),t=$("#t"),b=$("#b");
const fmt=(n,d=0)=>Number(n).toLocaleString("ru-RU",{maximumFractionDigits:d,minimumFractionDigits:d}).replace(/,/g,",");

function applyLang(){
  const D=I18N[L];document.documentElement.lang=L;
  document.querySelectorAll("[data-i]").forEach(el=>{const k=el.dataset.i;if(k==="h1html")el.innerHTML=D.h1html;else if(D[k]!==undefined)el.textContent=D[k]});
  document.querySelectorAll(".seg button").forEach(x=>x.classList.toggle("on",x.dataset.l===L));
  t.placeholder=D.ph;
  $("#steps").innerHTML="";D.steps.forEach((s,i)=>{const d=document.createElement("div");d.className="step";d.innerHTML=`<span class="n">${i+1}</span><div class="i">${s[0]}</div><b></b><p></p>`;d.querySelector("b").textContent=s[1];d.querySelector("p").textContent=s[2];$("#steps").appendChild(d)});
  if(!log.querySelector(".msg"))renderEmpty();
  if(STATS)renderStats();
}
function renderEmpty(){
  const D=I18N[L];log.innerHTML="";const e=document.createElement("div");e.className="empty";
  e.innerHTML=`<div class="big">✨</div><h4></h4><p></p><div class="chips"></div>`;
  e.querySelector("h4").textContent=D.emptyT;e.querySelector("p").textContent=D.emptyP;
  D.ex.forEach(([ic,q])=>{const c=document.createElement("div");c.className="chip";c.innerHTML="<span></span><div></div>";c.querySelector("span").textContent=ic;c.querySelector("div").textContent=q;c.onclick=()=>{t.value=q;send()};e.querySelector(".chips").appendChild(c)});
  log.appendChild(e);
}
function kpiCard(ic,c,v,l){return `<div class="kpi" style="--c:${c}"><div class="ic">${ic}</div><div class="v" data-to="${v.n}" data-d="${v.d||0}" data-suf="${v.s||""}">0</div><div class="l">${l}</div></div>`}
function countUp(){document.querySelectorAll(".kpi .v").forEach(el=>{const to=+el.dataset.to,d=+el.dataset.d,suf=el.dataset.suf;const t0=performance.now();
  const step=now=>{const p=Math.min(1,(now-t0)/1100),e=1-Math.pow(1-p,3);el.textContent=fmt(to*e,d)+suf;if(p<1)requestAnimationFrame(step)};requestAnimationFrame(step)})}
function renderStats(){
  const D=I18N[L],S=STATS;
  $("#kpis").innerHTML=kpiCard("📄","#2563eb",{n:S.deals},D.k[0])+kpiCard("💰","#14b8a6",{n:S.turnover_uzs/1e12,d:1,s:" "+D.tr.split(" ")[0]},D.k[1]+" ("+D.tr.split(" ")[1]+")")
   +kpiCard("🏢","#0ea5e9",{n:S.participants},D.k[2])+kpiCard("🤝","#8b5cf6",{n:S.brokers},D.k[3])+kpiCard("🌍","#f59e0b",{n:S.export_deals},D.k[4]);
  countUp();
  Object.values(charts).forEach(c=>c.destroy());charts={};
  Chart.defaults.font.family="Inter, system-ui, sans-serif";Chart.defaults.color="#64748b";Chart.defaults.font.size=11;
  const grid={color:"rgba(148,163,184,.15)"};
  const cy=$("#cYear").getContext("2d");const g=cy.createLinearGradient(0,0,0,220);g.addColorStop(0,"#2563eb");g.addColorStop(1,"#0ea5e9");
  charts.y=new Chart(cy,{data:{labels:S.by_year.map(x=>x.year),datasets:[
    {type:"bar",label:D.turn,data:S.by_year.map(x=>+(x.uzs/1e12).toFixed(1)),backgroundColor:g,borderRadius:8,maxBarThickness:46,yAxisID:"y"},
    {type:"line",label:D.deals,data:S.by_year.map(x=>x.deals),borderColor:"#14b8a6",backgroundColor:"#14b8a6",tension:.35,pointRadius:4,pointBackgroundColor:"#fff",pointBorderWidth:2,yAxisID:"y1"}]},
    options:{plugins:{legend:{position:"bottom",labels:{usePointStyle:true,boxWidth:8}}},scales:{y:{grid,beginAtZero:true},y1:{position:"right",grid:{display:false},beginAtZero:true,ticks:{callback:v=>fmt(v/1000)+"k"}},x:{grid:{display:false}}}}});
  const cm=$("#cMonth").getContext("2d");const g2=cm.createLinearGradient(0,0,0,170);g2.addColorStop(0,"rgba(14,165,233,.35)");g2.addColorStop(1,"rgba(14,165,233,0)");
  charts.m=new Chart(cm,{type:"line",data:{labels:S.by_month.map(x=>x.month),datasets:[{label:D.deals,data:S.by_month.map(x=>x.deals),borderColor:"#0ea5e9",backgroundColor:g2,fill:true,tension:.35,pointRadius:0,borderWidth:2}]},
    options:{plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{maxTicksLimit:8}},y:{grid,ticks:{callback:v=>fmt(v/1000)+"k"}}}}});
  charts.c=new Chart($("#cCat"),{type:"doughnut",data:{labels:S.by_category.map(x=>L==="uz"?(CATS_RU2UZ[x.name]||x.name):x.name),datasets:[{data:S.by_category.map(x=>+(x.uzs/1e12).toFixed(1)),backgroundColor:PAL,borderWidth:2,borderColor:"#fff",hoverOffset:6}]},
    options:{cutout:"62%",plugins:{legend:{position:"bottom",labels:{boxWidth:9,usePointStyle:true,font:{size:10}}},tooltip:{callbacks:{label:c=>` ${c.label}: ${c.parsed} ${D.tr}`}}}}});
  charts.r=new Chart($("#cReg"),{type:"bar",data:{labels:S.by_region.map(x=>x.name.replace(" viloyati","").replace(" shahri"," sh.").replace(" Respublikasi","")),datasets:[{label:D.deals,data:S.by_region.map(x=>x.deals),backgroundColor:PAL.map(c=>c+"cc"),borderRadius:6}]}
    ,options:{indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{grid,ticks:{callback:v=>fmt(v/1000)+"k"}},y:{grid:{display:false}}}}});
}
function el(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e}
function scroll(){log.scrollTop=log.scrollHeight}
function pickChart(queries){
  for(let i=queries.length-1;i>=0;i--){const q=queries[i];if(!q.data||q.data.length<2||q.data.length>25||!q.columns)continue;
    const cols=q.columns,rows=q.data;const isNum=j=>rows.every(r=>typeof r[j]==="number"||r[j]===null);
    let lab=cols.findIndex((c,j)=>!isNum(j));if(lab<0)lab=0;
    const bad=/(inn|stir|id|code|kod|year|month|_n$)/i;
    let val=-1;for(let j=0;j<cols.length;j++){if(j!==lab&&isNum(j)&&!bad.test(cols[j])){val=j;break}}
    if(val<0)continue;
    return {labels:rows.map(r=>String(r[lab]??"—").slice(0,26)),values:rows.map(r=>r[val]),name:cols[val]}}
  return null}
function addAnswer(j,ms){
  const D=I18N[L];const a=el("div","msg a");a.appendChild(el("div","txt"+(j.ok?"":" err"),j.answer||D.err));
  const meta=el("div","meta");meta.appendChild(el("span","tag","⏱ "+(j.seconds??(ms/1000).toFixed(1))+" s"));
  if(j.provider){const p=j.provider;const lab=p.startsWith("cache")?"⚡ cache":p==="instant"?"⚡ instant":"🤖 "+p.split("·")[0].split(":").pop().trim();meta.appendChild(el("span","tag m",lab))}
  if(j.queries&&j.queries.length)meta.appendChild(el("span","tag ok","✓ "+D.verified+" · "+j.queries.length));
  a.appendChild(meta);
  const ch=j.queries?pickChart(j.queries):null;
  if(ch){const box=el("div","achart");box.appendChild(el("div","t","📊 "+D.chartT+(ch.name.length>3&&!/^(cnt|cnt_|sum_|s$)/.test(ch.name)?" · "+ch.name.replace(/_/g," "):"")));const cv=document.createElement("canvas");const holder=el("div");holder.style.cssText="position:relative;height:"+Math.min(50+ch.labels.length*26,320)+"px";holder.appendChild(cv);box.appendChild(holder);a.appendChild(box);
    setTimeout(()=>new Chart(cv,{type:"bar",data:{labels:ch.labels,datasets:[{data:ch.values,backgroundColor:ch.labels.map((_,i)=>PAL[i%PAL.length]+"d0"),borderRadius:6,maxBarThickness:22}]},options:{indexAxis:"y",maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:"rgba(148,163,184,.15)"},ticks:{callback:v=>fmt(v)}},y:{grid:{display:false}}}}}),30)}
  if(j.queries&&j.queries.length){const d=el("details","basis");d.appendChild(el("summary","","🔎 "+D.basis+" ("+j.queries.length+")"));
    j.queries.forEach(q=>{const p=el("pre","sql");p.textContent=q.sql.trim();const r=el("span","r","\n→ "+q.rows+" "+D.rows);p.appendChild(r);d.appendChild(p)});a.appendChild(d)}
  log.appendChild(a);scroll()}
async function send(){
  const q=t.value.trim();if(!q||b.disabled)return;const D=I18N[L];
  if(log.querySelector(".empty"))log.innerHTML="";
  t.value="";autosize();log.appendChild(el("div","msg q",q));
  const w=el("div","msg a");w.innerHTML=`<div class="typing"><i></i><i></i><i></i>&nbsp;<span></span></div><div class="steps-mini"></div>`;
  w.querySelector(".typing span").textContent=D.thinking+"…";
  D.st.forEach((s,i)=>{const sp=el("span",i===0?"on":"",s);w.querySelector(".steps-mini").appendChild(sp)});
  log.appendChild(w);scroll();b.disabled=true;
  let k=0;const iv=setInterval(()=>{const sp=w.querySelectorAll(".steps-mini span");k=Math.min(k+1,sp.length-1);sp[k].classList.add("on")},2200);
  const t0=performance.now();
  try{const r=await fetch("/api/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q,history:hist})});
    const j=await r.json();w.remove();addAnswer(j,performance.now()-t0);if(j.ok)hist=[...hist,{q,a:j.answer}].slice(-2)}
  catch(e){w.remove();addAnswer({answer:D.err,ok:false},0)}
  clearInterval(iv);b.disabled=false;t.focus({preventScroll:true})}
function autosize(){t.style.height="auto";t.style.height=Math.min(t.scrollHeight,140)+"px"}
$("#f").onsubmit=e=>{e.preventDefault();send()};
t.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}});t.addEventListener("input",autosize);
$("#newBtn").onclick=()=>{hist=[];renderEmpty()};
document.querySelectorAll(".seg button").forEach(x=>x.onclick=()=>{L=x.dataset.l;try{localStorage.setItem("uzex_lang",L)}catch(e){}applyLang()});
applyLang();
fetch("/api/stats").then(r=>r.json()).then(s=>{STATS=s;renderStats()}).catch(()=>{});
const qp=new URLSearchParams(location.search).get("q");if(qp){t.value=qp;setTimeout(send,300)}
</script>
</body>
</html>"""
