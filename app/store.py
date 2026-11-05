"""Persistent chat memory + Q&A log in Postgres (Supabase). Falls back to RAM if DATABASE_URL is missing/down.

Schema `uzex` (isolated from anything else in the database):
  uzex.messages(id, chat_id, source, question, answer, ok, seconds, provider, queries jsonb, created_at)
History for the agent = last 2 successful Q/A of the chat after the last /new, within 6 hours.
"""
import json
import logging
import os
from collections import defaultdict, deque

log = logging.getLogger("store")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
_pool = None
_ram: dict[int, deque] = defaultdict(lambda: deque(maxlen=2))

DDL = """
CREATE SCHEMA IF NOT EXISTS uzex;
CREATE TABLE IF NOT EXISTS uzex.messages (
  id          bigserial PRIMARY KEY,
  chat_id     bigint      NOT NULL,
  source      text        NOT NULL DEFAULT 'tg',
  user_name   text,
  question    text        NOT NULL,
  answer      text,
  ok          boolean,
  seconds     real,
  provider    text,
  queries     jsonb,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_chat_idx ON uzex.messages (chat_id, id DESC);
"""


async def init():
    global _pool
    if not DATABASE_URL:
        log.warning("DATABASE_URL not set — memory kept in RAM only")
        return
    try:
        import asyncpg
        # Supabase transaction pooler (pgbouncer) => no prepared statement cache
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=4, statement_cache_size=0,
                                          command_timeout=10, timeout=15)
        async with _pool.acquire() as c:
            await c.execute(DDL)
        log.info("Postgres memory store ready")
    except Exception:  # noqa: BLE001
        log.exception("Postgres unavailable — using RAM memory")
        _pool = None


async def close():
    if _pool:
        await _pool.close()


async def history(chat_id: int) -> list[tuple[str, str]]:
    if _pool:
        try:
            rows = await _pool.fetch(
                """SELECT question, answer FROM uzex.messages
                   WHERE chat_id = $1 AND ok AND created_at > now() - interval '6 hours'
                     AND id > coalesce((SELECT max(id) FROM uzex.messages WHERE chat_id = $1 AND question = '/new'), 0)
                   ORDER BY id DESC LIMIT 2""", chat_id)
            return [(r["question"], r["answer"]) for r in reversed(rows)]
        except Exception:  # noqa: BLE001
            log.exception("history read failed")
    return list(_ram[chat_id])


async def save(chat_id: int, question: str, answer: str = "", ok: bool = True, seconds: float = 0.0,
               provider: str = "", queries: list | None = None, source: str = "tg", user_name: str = ""):
    if ok and question != "/new":
        _ram[chat_id].append((question, answer))
    if question == "/new":
        _ram.pop(chat_id, None)
    if not _pool:
        return
    try:
        await _pool.execute(
            """INSERT INTO uzex.messages (chat_id, source, user_name, question, answer, ok, seconds, provider, queries)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb)""",
            chat_id, source, user_name[:200], question[:4000], answer[:8000], ok, seconds, provider[:200],
            json.dumps(queries or [], ensure_ascii=False, default=str))
    except Exception:  # noqa: BLE001
        log.exception("save failed")


async def reset(chat_id: int):
    await save(chat_id, "/new", ok=False)
