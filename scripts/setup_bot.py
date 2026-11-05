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
        "Salom! Men UZEX birjasidagi bitimlar haqidagi savollarga javob beradigan AI-yordamchiman.\n\n"
        "📊 Bazada: 500 000 ta bitim (2022–2026), shartnomalar, kompaniyalar, brokerlar, dollar kursi.\n\n"
        "❓ Masalan, soʻrang:\n"
        "— 2025-yilda eng koʻp bitim tuzgan sotuvchi kim?\n"
        "— Karbamid boʻyicha 2024-yildagi jami summa qancha?\n\n"
        "✅ Javob faqat maʼlumotlardan: aniq raqam, nom, STIR.\n"
        "🔎 Har javob ostida u qayerdan olingani koʻrinadi.\n"
        "🚫 Maʼlumotda javob boʻlmasa — ochiq aytaman.\n\n"
        "Oʻzbek yoki rus tilida yozing 👇"
    ),
    "ru": (
        "Здравствуйте! Я AI-помощник: отвечаю на вопросы о сделках биржи UZEX.\n\n"
        "📊 В базе: 500 000 сделок (2022–2026), контракты, компании, брокеры, курс доллара.\n\n"
        "❓ Например, спросите:\n"
        "— Кто из продавцов заключил больше всего сделок в 2025 году?\n"
        "— Какая общая сумма сделок по карбамиду в 2024 году?\n\n"
        "✅ Ответ только по данным: точные цифры, названия, ИНН.\n"
        "🔎 Под каждым ответом видно, откуда он взят.\n"
        "🚫 Если в данных ответа нет — честно скажу.\n\n"
        "Пишите на русском или узбекском 👇"
    ),
}

SHORT = {
    # shown on the bot profile page and in shared links (max 120 chars)
    "": "UZEX birja bitimlari boʻyicha AI-yordamchi: aniq raqamlar, faqat maʼlumotlardan. Oʻzbek va rus tilida.",
    "ru": "AI-помощник по сделкам биржи UZEX: точные цифры строго по данным. На русском и узбекском.",
}

COMMANDS = {
    "": [
        ("start", "Boshlash"),
        ("examples", "Namuna savollar"),
        ("about", "Bot qanday ishlaydi"),
        ("new", "Yangi suhbat"),
        ("web", "Veb-versiya"),
    ],
    "ru": [
        ("start", "Начать"),
        ("examples", "Примеры вопросов"),
        ("about", "Как работает бот"),
        ("new", "Новый диалог"),
        ("web", "Веб-версия"),
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
