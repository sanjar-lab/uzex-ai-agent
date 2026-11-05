"""One process: FastAPI (web chat + REST API + Telegram webhook) and the Telegram bot.

Run:  python -m app.server        (PORT env, default 8000)
On a server (PUBLIC_URL / RENDER_EXTERNAL_URL set) the bot uses a webhook; locally it uses long polling.
"""
import asyncio
import hashlib
import logging
import os
import secrets
from contextlib import asynccontextmanager

from .config import load_env

load_env()

import uvicorn  # noqa: E402
from fastapi import FastAPI, Request, Response  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse  # noqa: E402
from telegram import Update  # noqa: E402
from telegram.ext import Application  # noqa: E402

from . import agent, db, llm, store, tg  # noqa: E402
from .web import PAGE  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("server")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PUBLIC_URL = (os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
# Telegram allows only [A-Za-z0-9_-] in the secret; Render's generated values may contain + / =, so hash them.
_raw_secret = os.getenv("WEBHOOK_SECRET") or TOKEN or secrets.token_hex(16)
WEBHOOK_SECRET = hashlib.sha256(_raw_secret.encode()).hexdigest()

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


async def warm_cache():
    """Answer the example questions once (persisted in Postgres) so example buttons reply instantly."""
    await asyncio.sleep(30)
    for lang in tg.T:
        for _, q in tg.T[lang]["examples"]:
            try:
                if await store.cache_get(agent.cache_key(q)):
                    continue
                r = await agent.ask(q)
                log.info("warm-cache: %s -> ok=%s %.1fs", q[:60], r.ok, r.seconds)
            except Exception:  # noqa: BLE001
                log.exception("warm-cache failed")
            await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global BOT
    await asyncio.to_thread(db.con)  # open DuckDB + warm up
    await asyncio.to_thread(db.run_sql, "SELECT count(*) FROM deals")
    log.info("LLM providers: %s", llm.configured())
    await store.init()
    pinger = asyncio.create_task(keep_awake()) if PUBLIC_URL else None
    warmer = asyncio.create_task(warm_cache()) if PUBLIC_URL and store.backend() == "postgres" else None

    if TOKEN:
        BOT = tg.build_bot(TOKEN, PUBLIC_URL)
        await BOT.initialize()
        await BOT.start()
        if PUBLIC_URL:
            try:
                await BOT.bot.set_webhook(f"{PUBLIC_URL}/tg/webhook", secret_token=WEBHOOK_SECRET,
                                          allowed_updates=tg.ALLOWED_UPDATES)
                log.info("Telegram webhook set: %s/tg/webhook", PUBLIC_URL)
            except Exception:  # noqa: BLE001 — never let Telegram issues kill the web service
                log.exception("set_webhook failed")
        else:
            await BOT.bot.delete_webhook()
            await BOT.updater.start_polling(allowed_updates=tg.ALLOWED_UPDATES)
            log.info("Telegram polling started")
    else:
        log.warning("TELEGRAM_BOT_TOKEN not set — web chat only")

    yield

    for task in (pinger, warmer):
        if task:
            task.cancel()
    await store.close()
    if BOT:
        if BOT.updater and BOT.updater.running:
            await BOT.updater.stop()
        await BOT.stop()
        await BOT.shutdown()


api = FastAPI(lifespan=lifespan, title="UZEX AI-agent", version="1.0")


@api.post("/tg/webhook", include_in_schema=False)
async def tg_webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET or not BOT:
        return Response(status_code=403)
    await BOT.update_queue.put(Update.de_json(await request.json(), BOT.bot))
    return Response(status_code=200)


@api.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    return PAGE


@api.get("/logo.png", include_in_schema=False)
async def logo():
    return FileResponse(os.path.join(ROOT, "assets", "logo.png"), media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@api.get("/api/stats")
async def api_stats():
    """Registry overview for the dashboard (cached)."""
    return await asyncio.to_thread(db.stats)


@api.get("/health")
async def health():
    return {"ok": True, "providers": len(llm.configured()), "bot": bool(BOT), "memory": store.backend()}


@api.post("/api/ask")
async def api_ask(request: Request):
    """{"question": "...", "history": [{"q": "...", "a": "..."}]} -> answer + the SQL it is based on."""
    body = await request.json()
    q = str(body.get("question", "")).strip()[:1000]
    if not q:
        return JSONResponse({"error": "empty question"}, status_code=400)
    hist = [(h.get("q", ""), h.get("a", "")) for h in body.get("history", [])[-2:] if isinstance(h, dict)]
    res = await agent.ask(q, hist)
    log.info("WEB Q: %s | %.1fs %s | A: %s", q[:200], res.seconds, res.provider, res.answer[:200].replace("\n", " "))
    asyncio.create_task(store.save(0, q, res.answer, res.ok, res.seconds, res.provider, res.queries, "web"))
    return {"answer": res.answer, "ok": res.ok, "seconds": round(res.seconds, 1), "provider": res.provider,
            "queries": [x for x in res.queries if not x.get("error")]}


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=int(os.getenv("PORT", "8000")), log_level="info")
