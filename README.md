# UZEX AI-agent (Telegram bot + web chat)

Answers RU/UZ questions about the UZEX deals registry strictly from data (DuckDB + LLM text-to-SQL with tool calling).
See [SOLUTION.md](SOLUTION.md) for the approach.

## Run locally
```
pip install -r requirements.txt
cp .env.example .env      # fill TELEGRAM_BOT_TOKEN, GEMINI_API_KEYS, GROQ_API_KEYS
python -m app.server      # web chat on http://localhost:8000, Telegram via long-polling
python -m app.cli "2025-yilda eng koʻp bitim tuzgan sotuvchi kim?"   # quick test
```
Rebuild the database from raw CSVs: `python build_db.py uzex_spot_data data/uzex.duckdb`.

## Deploy (Render, free)
1. Push this repo to GitHub (`.env` is git-ignored; `data/uzex.duckdb` is included).
2. Render → New → Blueprint → select the repo (uses `render.yaml`).
3. Set env vars `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEYS`, `GROQ_API_KEYS`. The webhook is registered automatically
   using `RENDER_EXTERNAL_URL`.
4. Keep it awake: UptimeRobot / cron-job.org GET `https://<app>.onrender.com/health` every 5 min.
