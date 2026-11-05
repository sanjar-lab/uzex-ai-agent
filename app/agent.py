"""Text-to-SQL agent: question (RU/UZ) -> tool calls on DuckDB -> grounded answer."""
import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field

from . import db, llm

log = logging.getLogger("agent")

MAX_STEPS = 10
ANSWER_DEADLINE = 80  # seconds; the jury allows 90s per answer

SYSTEM_PROMPT = r"""
You are the UZEX deals analyst: an AI agent that answers questions about the commodity-exchange deals registry
(spot.uzex.uz format). Questions come in Uzbek (Latin or Cyrillic) or Russian.

GOLDEN RULES (violating them disqualifies the team):
1. Every number, company, INN, product, code, date in your answer MUST come from tool results in THIS conversation.
   Never use outside knowledge, never estimate, never round away precision that matters.
2. Before answering any factual question call run_sql (and find_entity for names). Check your SQL result makes sense.
   Every extra claim (e.g. "excluding cancelled deals the figure is …", "this company has no cancelled deals",
   shares, differences, sums of rows) needs its own query — compute it in SQL, never in your head.
   An automatic checker compares every number in your answer with the tool results and rejects unverified ones.
3. If the data has no answer (0 rows, entity not found, field doesn't exist in the data such as phone numbers,
   profit, employees, weather; period outside 03.01.2022–30.10.2026), say so openly:
   UZ: "Maʼlumotlarda bu savolga javob yoʻq." RU: "В данных нет ответа на этот вопрос." — then one line on what
   the data does contain. Do NOT invent a substitute answer. If a name is ambiguous, list the candidates found.
4. Reply in the language and script of the question (Uzbek Latin → Uzbek Latin, Uzbek Cyrillic → Uzbek Cyrillic,
   Russian → Russian). The required answer language is given in [brackets] after each question — obey it.
   Copy company names, product names, statuses and codes EXACTLY as they appear in the data (keep Cyrillic as Cyrillic,
   Latin as Latin, quotes included); never transliterate them. You may add a short translation in parentheses.
   For a specific deal/contract always state its number (deal_id / contract_id).
5. Format: plain text (no markdown, no **, no tables with |). First line = the direct answer with exact figures.
   Numbers with space thousand separators: 1 234 567 890,5. Always give units (so‘m/сум, USD, tonna/тонна, kg, l…).
   Then 1–3 short lines "how it was computed": period, filters (status, currency, product variants included).
   Keep it short. Do not show SQL (the app shows it automatically).

DATA (DuckDB). Data covers 2022-01-03 … 2026-10-30; statuses are as of 30.10.2026 ("today" in the data).
"This year" = 2026, "last year" = 2025.

TABLE deals — one row per deal (500 000 rows). Denormalized, usually no joins needed:
  deal_id BIGINT (Номер сделки / bitim raqami), deal_date DATE, deal_time VARCHAR 'HH:MM:SS', deal_year INT, deal_month INT,
  trade_type ('Английский аукцион'|'Двусторонний аукцион'|'Обратный аукцион'),
  quantity DOUBLE (lots bought), lot DOUBLE (units per lot), volume DOUBLE (= quantity*lot, in `unit`),
  unit ('тонна','килограмм','литр','штука','куб.метр','кв.метр','метр'),
  amount DOUBLE (deal sum in CONTRACT currency), currency ('Узбекский сум'|'Доллар США'),
  usd_rate DOUBLE (UZS per 1 USD on deal_date), amount_uzs DOUBLE (sum in UZS; USD deals converted), amount_usd DOUBLE,
  unit_price DOUBLE (= amount/volume, contract currency), start_price DOUBLE (start price per unit, contract currency),
  contract_id BIGINT (Номер контракта), product_name VARCHAR (full registry name incl. attributes),
  product_base VARCHAR (product name from contract card), product_norm VARCHAR (lowercase Latin transliteration of product_name),
  product_group ('Высоколиквидные товары'|'Прочие товары'),
  product_category ('Сельскохозяйственная продукция','Нефтепродукты','Продовольственные товары','Строительные материалы',
                    'Полимерная продукция','Химическая продукция','Металлопродукция','Промышленные товары'),
  industry ('Сельское хозяйство','Нефтегазовая промышленность','Пищевая промышленность','Строительная индустрия',
            'Химическая промышленность','Металлургия','Лесная промышленность','Текстильная промышленность',
            'Электротехническая промышленность','Машиностроение'),
  tnved_code VARCHAR (Код ТН ВЭД / TIF TN kodi),
  region VARCHAR (seller warehouse region, Uzbek Latin: 'Toshkent shahri','Toshkent viloyati','Andijon viloyati',
          'Buxoro viloyati','Farg‘ona viloyati','Jizzax viloyati','Xorazm viloyati','Namangan viloyati','Navoiy viloyati',
          'Qashqadaryo viloyati','Qoraqalpog‘iston Respublikasi','Samarqand viloyati','Sirdaryo viloyati','Surxondaryo viloyati'
          — note the ‘ character; safer: region ILIKE 'farg%'),
  contract_type ('Внутренний'|'Экспортный'), contract_form ('Спот'|'Форвард'|'Фьючерс'),
  status ('Исполнен','Исполнен(Частично)','Оплачен','Ждёт оплату','Заключен','Не подписан','Новый','Аннулирован(Не оплачен)'),
  seller_inn VARCHAR, seller_name, buyer_inn VARCHAR, buyer_name,
  seller_broker VARCHAR (code 'BK001'…), seller_broker_name, buyer_broker, buyer_broker_name,
  payment_date DATE (NULL = not paid), delivery_date DATE (NULL = not delivered), delivered_lots DOUBLE.

TABLE contracts — contract cards (6 616): contract_id, product_base, brand, size, grade, ptype, pclass, tnved_code,
  product_group, product_category, industry, unit, lot, currency, base_price (per unit at registration), deposit_pct ('10 %'),
  delivery_basis ('EXW','FCA','CPT','DAP'), region (Russian: 'г. Ташкент','Самаркандская область',…), warehouse_address,
  trade_type, contract_type, contract_form, payment_term_days (days from deal to pay), delivery_term_days (days from payment
  to deliver), packaging, seller_inn, registered_date DATE, valid_until DATE, product_norm.
TABLE participants (14 392 companies): inn VARCHAR(9 digits), company_name, name_norm, region (Uzbek Latin), activity
  ('Производитель','Торговая компания','Кластер','Перерабатывающее предприятие','Строительная компания',
  'Транспортная компания','Производственное предприятие'), role ('Продавец'|'Покупатель'), vat_payer ('Да'|'Нет').
TABLE brokers (120): broker_code ('BK001'), broker_name, name_norm, broker_inn, region.
TABLE usd_rates: rate_date DATE (every calendar day), usd_rate (UZS per 1 USD).
TABLE products: product_base, base_norm, tnved_code, product_category, industry, unit, deals_count, name_variants.

HOW TO COMPUTE:
- All ID/INN/code columns are VARCHAR except deal_id/contract_id: seller_inn = '921912462'.
- Money totals across deals: use amount_uzs (UZS) by default; amount_usd if asked in dollars. Never SUM(amount) across
  mixed currencies. For a single deal report amount in its own currency (and UZS equivalent for USD deals).
- Volume: SUM(volume) only within one unit; if units differ, group by unit.
- Average price of a product: SUM(amount)/SUM(volume) (weighted) within one currency+unit; mention it's weighted.
  Price growth in auction: (unit_price - start_price)/start_price.
- Cancelled deals ('Аннулирован(Не оплачен)') did not happen. MANDATORY: if the question doesn't specify statuses, the
  MAIN figure is computed over ALL deals (no status filter), and when cancelled deals are in the selection add one line
  with the figure excluding them. For rankings use all deals for the main ranking (and say if excluding cancelled
  changes the leader). Never silently drop cancelled deals.
- "Executed/ijro etilgan" = status IN ('Исполнен','Исполнен(Частично)'). Paid = payment_date IS NOT NULL.
- Questions about contracts themselves (how many registered, valid until, base price, payment/delivery terms,
  deposit, packaging, warehouse) → table contracts (registered_date, valid_until …), NOT distinct contract_id in deals.
  "Contracts that had deals" is a different question — say which one you answered if ambiguous.
  Same for companies: "how many companies/participants" → participants table; "how many active sellers" → deals.
- Export = contract_type='Экспортный' (these are in USD). Spot/forward/futures = contract_form.
- Product names are inconsistent across sellers (case, hyphens, word order, attributes): 'Хлопок сырец (спот)' vs
  'Хлопок-сырец (спот)', 'ПОРТЛАНДЦЕМЕНТ' vs 'Портландцемент ЦЕМ I 42,5 Н', 'Дизельное топливо' vs 'Топливо дизельное',
  'Мука' vs 'МУКА ПШЕНИЧНАЯ'. ALWAYS first call find_entity(kind='product') to see variants, then filter with
  product_norm LIKE '%stem%' (Latin translit, e.g. '%xlopok%sirets%', '%portlandtsement%', '%dizel%', '%karbamid%',
  '%selitra%', '%bugdoy%' does NOT exist — data is Russian: wheat='%pshenits%', flour='%muka%', sugar='%saxar%',
  cotton='%xlopok%', cement='%tsement%', gasoline='%benzin%', diesel='%dizel%', LPG='%sjijenn%gaz%' or '%propan%')
  or with product_base IN (...) / tnved_code. Say in the answer which variants were included.
  Translate Uzbek product words to Russian first (paxta=хлопок, bug‘doy=пшеница, un=мука, shakar=сахар, sement=цемент,
  benzin=бензин, dizel yoqilg‘isi=дизельное топливо, o‘g‘it/karbamid=карбамид, selitra=селитра, yog‘=масло,
  polietilen=полиэтилен, armatura=арматура, g‘isht=кирпич, suyultirilgan gaz=сжиженный газ, ko‘mir=уголь, mis=медь).
- Companies: names may be Cyrillic or Latin with different legal forms. Resolve with find_entity(kind='company'), then
  filter by INN. Same for brokers (find_entity kind='broker', filter by broker code).
- Rankings: ORDER BY … DESC LIMIT N; include names AND INN/codes. Ties: mention them.
- Dates: use deal_date BETWEEN DATE '2025-01-01' AND DATE '2025-12-31', or deal_year/deal_month. Quarter: quarter(deal_date).

UZBEK/RUSSIAN TERMS: bitim/сделка=deal, sotuvchi/продавец=seller, xaridor/покупатель=buyer, summa=amount, hajm=volume,
narx=price, boshlang‘ich narx=start_price, shartnoma=contract, bekor qilingan/аннулирован=cancelled,
to‘langan=paid, yetkazib berilgan=delivered, broker idorasi=broker, viloyat=region, STIR/ИНН=INN, oy=month, chorak=quarter,
eng ko‘p=the most, o‘rtacha=average, jami=total, nechta=how many.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Run ONE read-only DuckDB SQL query (SELECT/WITH) over tables deals, contracts, participants, "
                           "brokers, usd_rates, products. Returns at most 50 rows as TSV. Aggregate in SQL.",
            "parameters": {
                "type": "object",
                "properties": {"sql": {"type": "string", "description": "DuckDB SQL query"}},
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_entity",
            "description": "Fuzzy search (Cyrillic/Latin/typos) for a company, broker or product name; also accepts an "
                           "INN, broker code or TN VED code. Returns best candidates with scores and deal counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["company", "broker", "product"]},
                    "query": {"type": "string", "description": "name / part of the name / INN / code"},
                },
                "required": ["kind", "query"],
            },
        },
    },
]


@dataclass
class Result:
    answer: str
    queries: list[dict] = field(default_factory=list)  # [{'sql':..., 'rows': n, 'error':...}]
    provider: str = ""
    seconds: float = 0.0
    ok: bool = True
    unverified: list[str] = field(default_factory=list)


_NUM_ANS = re.compile(r"(?<![\w.,])-?\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?(?![\d])|(?<![\w.,])-?\d+(?:[.,]\d+)?(?![\d])")
_NUM_TOOL = re.compile(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", re.I)
_DATES = re.compile(r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}:\d{2}(?::\d{2})?\b")


def _parse_answer_number(s: str) -> tuple[float, int]:
    s = re.sub(r"[   ]", "", s).replace(",", ".")
    dec = len(s.split(".")[1]) if "." in s else 0
    return float(s), dec


def ungrounded_numbers(answer: str, sources: list[str]) -> list[str]:
    """Numbers in the answer that can't be matched (allowing rounding, %, k/1000 conversions) to tool output."""
    pool: list[float] = []
    for src in sources:
        for m in _NUM_TOOL.findall(_DATES.sub(" ", src)):
            try:
                pool.append(float(m))
            except ValueError:
                pass
        # dates in tool output may be quoted as parts (day, month, year) in the answer
        for d in _DATES.findall(src):
            pool += [float(x) for x in re.findall(r"\d+", d)]
    text = _DATES.sub(" ", answer)
    text = re.sub(r"\b(BK)\d+", " ", text)  # broker codes are checked via strings
    bad = []
    for m in _NUM_ANS.findall(text):
        try:
            a, dec = _parse_answer_number(m)
        except ValueError:
            continue
        if abs(a) <= 12 and a == int(a) or 2022 <= a <= 2026 and a == int(a):
            continue  # ordinal words, months, quarters, years
        tol_abs = 0.5 * 10 ** (-dec) + 1e-9
        ok = False
        for t in pool:
            for f in (1, 100, 0.01, 1000, 0.001, 1e6, 1e-6, 1e9, 1e-9):
                v = t * f
                if abs(a - v) <= tol_abs or (v != 0 and abs(a - v) / abs(v) < 0.0015):
                    ok = True
                    break
            if ok:
                break
        if not ok:
            bad.append(m.strip())
    return bad


def detect_lang(text: str) -> str:
    if re.search(r"[ўқғҳЎҚҒҲ]", text):
        return "uz_cyr"
    if re.search(r"[а-яА-ЯёЁ]", text):
        # Uzbek words written in Cyrillic without special letters are rare enough
        if re.search(r"\b(нечта|қанча|канча|бўйича|йил|сотувчи|харидор|битим)\b", text, re.I):
            return "uz_cyr"
        return "ru"
    return "uz"


LANG_NAMES = {"uz": "Uzbek, Latin script", "uz_cyr": "Uzbek, Cyrillic script", "ru": "Russian"}

NO_ANSWER = {
    "uz": "Kechirasiz, hozir javobni tekshirib boʻlmadi (AI xizmati band). Iltimos, savolni qayta yuboring.",
    "uz_cyr": "Кечирасиз, ҳозир жавобни текшириб бўлмади (AI хизмати банд). Илтимос, саволни қайта юборинг.",
    "ru": "Извините, сейчас не удалось проверить ответ (AI-сервис перегружен). Пожалуйста, отправьте вопрос ещё раз.",
}


async def _exec_tool(name: str, args: dict, queries: list[dict]) -> str:
    if name == "run_sql":
        sql = args.get("sql", "")
        res = await asyncio.to_thread(db.run_sql, sql)
        queries.append({"tool": "sql", "sql": sql, "rows": len(res.get("rows", [])), "error": res.get("error")})
        return "ERROR: " + res["error"] if "error" in res else res["text"]
    if name == "find_entity":
        res = await asyncio.to_thread(db.find_entity, args.get("kind", ""), args.get("query", ""))
        queries.append({"tool": "find", "sql": f"find_entity({args.get('kind')}, {args.get('query')!r})",
                        "rows": len(res.get("rows", [])), "error": res.get("error")})
        return "ERROR: " + res["error"] if "error" in res else res["text"]
    return f"ERROR: unknown tool {name}"


async def ask(question: str, history: list[tuple[str, str]] | None = None) -> Result:
    t0 = time.time()
    deadline = t0 + ANSWER_DEADLINE
    lang = detect_lang(question)
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for q, a in (history or [])[-2:]:
        messages += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
    messages.append({"role": "user", "content": f"{question}\n\n[Answer language: {LANG_NAMES[lang]}]"})
    queries: list[dict] = []
    prefer = None
    provider_name = ""
    nudged = False
    verify_rounds = 0

    for step in range(MAX_STEPS):
        last = step == MAX_STEPS - 1 or time.time() > deadline - 20
        if last:
            messages.append({"role": "user", "content": "Time is up: answer now using ONLY the tool results above. "
                             "If they are insufficient, say the data does not contain the answer."})
        try:
            msg, prov = await llm.chat(messages, None if last else TOOLS, prefer=prefer, deadline=deadline)
        except llm.AllProvidersFailed as e:
            log.error("all providers failed: %s", e)
            return Result(NO_ANSWER[lang], queries, provider_name, time.time() - t0, ok=False)
        prefer = prov.name
        provider_name = f"{prov.name} · {prov.model}"
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            text = (msg.get("content") or "").strip()
            # Guard: a factual answer without any successful data lookup is not allowed.
            if not any(not q.get("error") for q in queries) and not nudged and not last:
                nudged = True
                messages.append({"role": "user", "content": "You have not checked the data yet. Use the tools to verify "
                                 "before answering (unless this is a greeting / not a data question)."})
                continue
            # Guard 2: every number in the answer must be present in tool results (or the question).
            bad = ungrounded_numbers(text, [m.get("content") or "" for m in messages if m.get("role") == "tool"]
                                     + [question])
            if bad and verify_rounds < 2 and not last and time.time() < deadline - 15:
                verify_rounds += 1
                log.info("ungrounded numbers %s -> asking model to verify", bad)
                messages.append({"role": "user", "content":
                                 "Automatic check FAILED: these numbers in your answer do not appear in any tool result: "
                                 + ", ".join(bad) + ". Get each of them with a SQL query (compute in SQL), or remove the "
                                 "claim. Then give the final answer again (same language, same format)."})
                continue
            return Result(_clean(text), queries, provider_name, time.time() - t0, unverified=bad)
        for tc in calls:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            out = await _exec_tool(fn.get("name", ""), args, queries)
            messages.append({"role": "tool", "tool_call_id": tc["id"], "name": fn.get("name", ""), "content": out[:8000]})
    return Result(NO_ANSWER[lang], queries, provider_name, time.time() - t0, ok=False)


def _clean(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return text.strip()
