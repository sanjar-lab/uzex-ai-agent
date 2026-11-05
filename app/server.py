"""One process: FastAPI web chat + Telegram bot (webhook on servers, polling locally).

Run:  python -m app.server        (PORT env, default 8000)
"""
import asyncio
import hashlib
import html
import logging
import os
import secrets
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from .config import load_env

load_env()

import uvicorn  # noqa: E402
from fastapi import FastAPI, Request, Response  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: E402
from telegram import Update  # noqa: E402
from telegram.constants import ChatAction, ParseMode  # noqa: E402
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters  # noqa: E402

from . import agent, db, llm, store  # noqa: E402
from .web import PAGE  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("server")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PUBLIC_URL = (os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
# Telegram allows only [A-Za-z0-9_-] (1-256 chars); Render's generated values may contain + / =, so hash them.
_raw_secret = os.getenv("WEBHOOK_SECRET") or TOKEN or secrets.token_hex(16)
WEBHOOK_SECRET = hashlib.sha256(_raw_secret.encode()).hexdigest()
HISTORY: dict[int, deque] = defaultdict(lambda: deque(maxlen=2))

START_TEXT = (
    "👋 <b>UZEX AI-agent</b> — birja bitimlari reyestri boʻyicha savollarga faqat maʼlumotlar asosida javob beradi.\n"
    "Агент отвечает на вопросы о биржевых сделках строго по данным реестра (500 000 сделок, 01.2022–10.2026).\n\n"
    "Savol bering / Задайте вопрос, masalan / например:\n"
    "• 2025-yilda eng koʻp bitim tuzgan sotuvchi kim?\n"
    "• Какая общая сумма сделок по карбамиду в 2024 году?\n"
    "• 104512-sonli shartnoma boʻyicha nechta bitim boʻlgan?\n"
    "• Какой брокер покупателя провёл больше всего сделок в Самарканде?\n\n"
    "Har bir javob ostida u qaysi SQL soʻrov(lar) asosida olingani koʻrsatiladi.\n"
    "Под каждым ответом видно, на каких SQL-запросах он основан.\n"
    "/new — yangi suhbat / новый диалог"
)

ABOUT_TEXT = (
    "ℹ️ <b>Bot qanday ishlaydi / Как работает бот</b>\n\n"
    "<b>Maʼlumotlar:</b> UZEX reyestri — 500 000 bitim (03.01.2022–30.10.2026), 6 616 shartnoma, "
    "14 392 ishtirokchi, 120 broker, kunlik dollar kursi. Hammasi DuckDB bazasida.\n\n"
    "<b>Usul:</b> AI savolni tahlil qiladi → kompaniya/tovar/broker nomini bazadan topadi (kirill-lotin moslash) → "
    "SQL soʻrov bajaradi → faqat olingan natija asosida javob yozadi.\n\n"
    "<b>Ishonchlilik:</b> maʼlumot tekshirilmasa javob berilmaydi; maʼlumotda yoʻq narsa so‘ralsa — "
    "«Maʼlumotlarda javob yoʻq». Har javob ostida SQL asos koʻrsatiladi (🔎 blokni bosing).\n\n"
    "<b>Данные:</b> реестр UZEX, 500 000 сделок. <b>Метод:</b> AI → поиск сущностей → SQL → ответ только по "
    "результату запроса. Если данных нет — бот говорит об этом прямо. Под каждым ответом — SQL-основание.\n\n"
    "<i>Gemini + Groq · DuckDB · Python</i>"
)

THINKING = {"uz": "⏳ Maʼlumotlar tekshirilmoqda…", "uz_cyr": "⏳ Маълумотлар текширилмоқда…", "ru": "⏳ Проверяю данные…"}
BASIS = {"uz": "Asos", "uz_cyr": "Асос", "ru": "Основание"}


def basis_block(res: agent.Result, lang: str, limit: int = 2500) -> str:
    ok = [q for q in res.queries if not q.get("error")]
    if not ok:
        return ""
    parts, used = [], 0
    for q in ok[-4:]:
        s = q["sql"].strip()
        if used + len(s) > limit:
            s = s[: max(0, limit - used)] + "…"
        parts.append(f"{html.escape(s)}\n→ {q['rows']} rows")
        used += len(s)
        if used >= limit:
            break
    head = f"🔎 {BASIS[lang]}: {len(ok)} query · {res.seconds:.0f}s"
    return f"\n\n<blockquote expandable><b>{head}</b>\n<code>" + "\n\n".join(parts) + "</code></blockquote>"


# ---------------- Telegram ----------------
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await store.reset(update.effective_chat.id)
    await update.effective_message.reply_text(START_TEXT, parse_mode=ParseMode.HTML)


async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(ABOUT_TEXT, parse_mode=ParseMode.HTML)


async def cmd_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await store.reset(update.effective_chat.id)
    await update.effective_message.reply_text("🆕 Yangi suhbat / Новый диалог")


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    q = (msg.text or "").strip()
    if not q:
        return
    chat_id = update.effective_chat.id
    lang = agent.detect_lang(q)
    placeholder = await msg.reply_text(THINKING[lang])

    async def typing():
        while True:
            try:
                await ctx.bot.send_chat_action(chat_id, ChatAction.TYPING)
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(4.5)

    t = asyncio.create_task(typing())
    try:
        res = await agent.ask(q, await store.history(chat_id))
    except Exception:  # noqa: BLE001
        log.exception("agent failed")
        res = agent.Result(agent.NO_ANSWER[lang], ok=False)
    finally:
        t.cancel()
    u = update.effective_user
    asyncio.create_task(store.save(chat_id, q, res.answer, res.ok, res.seconds, res.provider, res.queries, "tg",
                                   (u.username or u.full_name) if u else ""))
    text = html.escape(res.answer)[:3300] + basis_block(res, lang)
    log.info("Q[%s]: %s | %.1fs %s | A: %s", chat_id, q[:200], res.seconds, res.provider, res.answer[:200].replace("\n", " "))
    try:
        await placeholder.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception:  # noqa: BLE001
        log.exception("edit failed, sending plain")
        await msg.reply_text(res.answer[:4000])


def build_bot() -> Application | None:
    if not TOKEN:
        log.warning("TELEGRAM_BOT_TOKEN not set — web chat only")
        return None
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


BOT: Application | None = None


async def keep_awake():
    """Render free instances sleep after 15 min without inbound traffic: ping our own public URL every 10 min."""
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            await asyncio.sleep(600)
            try:
                r = await client.get(f"{PUBLIC_URL}/health")
                log.info("keep-awake ping: %s", r.status_code)
            except Exception as e:  # noqa: BLE001
                log.warning("keep-awake ping failed: %s", e)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global BOT
    await asyncio.to_thread(db.con)  # open DB / warm up
    await asyncio.to_thread(db.run_sql, "SELECT count(*) FROM deals")
    log.info("LLM providers: %s", llm.configured())
    await store.init()
    pinger = asyncio.create_task(keep_awake()) if PUBLIC_URL else None
    BOT = build_bot()
    if BOT:
        await BOT.initialize()
        await BOT.start()
        if PUBLIC_URL:
            url = f"{PUBLIC_URL}/tg/webhook"
            try:
                await BOT.bot.set_webhook(url, secret_token=WEBHOOK_SECRET, drop_pending_updates=False,
                                          allowed_updates=["message"])
                log.info("Telegram webhook set: %s", url)
            except Exception:  # noqa: BLE001 — never let Telegram issues kill the web service
                log.exception("set_webhook failed")
        else:
            await BOT.bot.delete_webhook()
            await BOT.updater.start_polling(allowed_updates=["message"])
            log.info("Telegram polling started")
    yield
    if pinger:
        pinger.cancel()
    await store.close()
    if BOT:
        if BOT.updater and BOT.updater.running:
            await BOT.updater.stop()
        await BOT.stop()
        await BOT.shutdown()


api = FastAPI(lifespan=lifespan, title="UZEX AI agent")


@api.post("/tg/webhook")
async def tg_webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET or not BOT:
        return Response(status_code=403)
    data = await request.json()
    await BOT.update_queue.put(Update.de_json(data, BOT.bot))
    return Response(status_code=200)


@api.get("/", response_class=HTMLResponse)
async def index():
    return PAGE


@api.get("/logo.png")
async def logo():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png"),
                        media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


@api.get("/health")
async def health():
    return {"ok": True, "providers": len(llm.configured()), "bot": bool(BOT)}


@api.post("/api/ask")
async def api_ask(request: Request):
    body = await request.json()
    q = str(body.get("question", "")).strip()[:1000]
    if not q:
        return JSONResponse({"error": "empty question"}, status_code=400)
    hist = [(h.get("q", ""), h.get("a", "")) for h in body.get("history", [])[-2:] if isinstance(h, dict)]
    res = await agent.ask(q, hist)
    log.info("WEB Q: %s | %.1fs %s | A: %s", q[:200], res.seconds, res.provider, res.answer[:200].replace("\n", " "))
    asyncio.create_task(store.save(0, q, res.answer, res.ok, res.seconds, res.provider, res.queries, "web"))
    return {"answer": res.answer, "ok": res.ok, "seconds": round(res.seconds, 1), "provider": res.provider,
            "queries": [q for q in res.queries if not q.get("error")]}


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=int(os.getenv("PORT", "8000")), log_level="info")
