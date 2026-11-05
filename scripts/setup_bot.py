"""One-time Telegram bot profile setup: name, descriptions (UZ default + RU), command menu.

python scripts/setup_bot.py            (reads TELEGRAM_BOT_TOKEN from .env)

The profile photo and description picture can only be set in @BotFather:
  /setuserpic  -> assets/logo.png
  /setdescription -> "Edit description picture" -> assets/banner.png  (640x360)
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import load_env  # noqa: E402

load_env()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    sys.exit("TELEGRAM_BOT_TOKEN is empty in .env")

NAME = "UZEX AI-agent"

DESCRIPTION = {
    # shown in the empty chat before the user presses START (max 512 chars)
    "": (
        "UZEX birja bitimlari reyestri boʻyicha AI-agent.\n\n"
        "• 500 000 bitim (2022–2026), shartnomalar, ishtirokchilar, brokerlar, dollar kursi\n"
        "• Savolni oʻzbek (lotin/kirill) yoki rus tilida bering\n"
        "• Javob faqat maʼlumotlar asosida: aniq raqam, nom, STIR, kod\n"
        "• Maʼlumot boʻlmasa — ochiq aytadi, oʻylab topmaydi\n"
        "• Har bir javob ostida u asoslangan SQL soʻrov koʻrsatiladi\n\n"
        "Boshlash uchun START ni bosing."
    ),
    "ru": (
        "AI-агент по реестру биржевых сделок UZEX.\n\n"
        "• 500 000 сделок (2022–2026), контракты, участники, брокеры, курс доллара\n"
        "• Спрашивайте на русском или узбекском (латиница/кириллица)\n"
        "• Ответ строго по данным: точные цифры, названия, ИНН, коды\n"
        "• Если в данных ответа нет — так и скажет, без выдумок\n"
        "• Под каждым ответом виден SQL-запрос, на котором он основан\n\n"
        "Нажмите START, чтобы начать."
    ),
}

SHORT = {
    # shown on the bot profile page and in shared links (max 120 chars)
    "": "Birja bitimlari boʻyicha savollarga faqat maʼlumotlar asosida javob beruvchi AI-agent. UZ / RU",
    "ru": "AI-агент: отвечает на вопросы о биржевых сделках строго по данным реестра. RU / UZ",
}

COMMANDS = {
    "": [
        ("start", "Boshlash va savol namunalari"),
        ("about", "Bot qanday ishlaydi, maʼlumotlar manbasi"),
        ("new", "Yangi suhbat (kontekstni tozalash)"),
    ],
    "ru": [
        ("start", "Начать и примеры вопросов"),
        ("about", "Как работает бот, источник данных"),
        ("new", "Новый диалог (сбросить контекст)"),
    ],
}


def call(method: str, **params):
    data = json.dumps(params).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.load(r)
    except urllib.error.HTTPError as e:
        res = json.load(e)
    print(f"{method:24} {params.get('language_code', '') or 'default':8} ->", "OK" if res.get("ok") else res)
    return res


me = call("getMe")
print("bot:", "@" + me.get("result", {}).get("username", "?"))
call("setMyName", name=NAME)
for lang in ("", "ru"):
    kw = {"language_code": lang} if lang else {}
    call("setMyDescription", description=DESCRIPTION[lang], **kw)
    call("setMyShortDescription", short_description=SHORT[lang], **kw)
    call("setMyCommands", commands=[{"command": c, "description": d} for c, d in COMMANDS[lang]], **kw)
print("\nNow in @BotFather: /setuserpic -> assets/logo.png ; /setdescription -> picture -> assets/banner.png")
