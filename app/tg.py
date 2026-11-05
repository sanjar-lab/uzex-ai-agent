"""Telegram UI: texts (UZ/RU by the user's Telegram language), menu keyboard, example-question buttons, handlers.

Answers themselves are always in the language of the question (handled by the agent).
"""
import asyncio
import html
import logging

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters)

from . import agent, store

log = logging.getLogger("tg")
ALLOWED_UPDATES = ["message", "callback_query"]
PUBLIC_URL = ""  # set by server

# ------------------------------------------------------------------ texts
T = {
    "uz": {
        "start": (
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Men — <b>UZEX AI-agent</b>. Birja bitimlari reyestri boʻyicha savollaringizga "
            "<b>faqat maʼlumotlar asosida</b> javob beraman.\n\n"
            "📊 <b>Bazada:</b> 500 000 ta bitim (03.01.2022 – 30.10.2026), 6 616 ta shartnoma, "
            "14 392 ta kompaniya, 120 ta broker va kunlik dollar kursi.\n\n"
            "<b>Nimalarni soʻrash mumkin:</b>\n"
            "• reytinglar — eng faol sotuvchi, xaridor, broker\n"
            "• summa, hajm va oʻrtacha narxlar\n"
            "• kompaniya (nomi yoki STIR), shartnoma va bitim raqami boʻyicha\n"
            "• eksport, bitim holatlari, viloyatlar va davrlar kesimida\n\n"
            "🔎 Har javob ostida u qaysi soʻrov asosida olingani koʻrsatiladi.\n"
            "🚫 Maʼlumotda javob boʻlmasa — buni ochiq aytaman.\n\n"
            "Savolingizni <b>oʻzbek</b> yoki <b>rus</b> tilida yozing 👇"
        ),
        "examples_title": "💡 <b>Namuna savollar</b> — bosing, javob darhol keladi:",
        "examples": [
            ("🏆 Eng faol sotuvchi (2025)", "2025-yilda eng koʻp bitim tuzgan sotuvchi kim?"),
            ("🧪 Karbamid savdosi (2024)", "Karbamid boʻyicha 2024-yildagi jami savdo summasi qancha?"),
            ("🌍 Eksport: yetakchi viloyat", "Qaysi viloyatda eksport bitimlari eng koʻp?"),
            ("❌ Bekor qilingan bitimlar (2026)", "2026-yilda nechta bitim bekor qilingan?"),
            ("💵 Dollar kursi (15.03.2025)", "2025-yil 15-martdagi dollar kursi qancha boʻlgan?"),
            ("🌱 Paxta: eng yirik xaridor (2025)", "2025-yilda eng koʻp paxta xom ashyosi sotib olgan xaridor kim?"),
        ],
        "about": (
            "ℹ️ <b>UZEX AI-agent qanday ishlaydi</b>\n\n"
            "<b>1. Maʼlumotlar.</b> UZEX birja bitimlari reyestri: 500 000 ta bitim (03.01.2022 – 30.10.2026), "
            "6 616 ta shartnoma kartochkasi, 14 392 ta kompaniya, 120 ta broker, kunlik dollar kursi.\n\n"
            "<b>2. Savolni tushunish.</b> AI savolni tahlil qiladi va kompaniya, tovar yoki broker nomini bazadan "
            "topadi — kirill va lotin yozuvlari, turli imlolar mos keltiriladi.\n\n"
            "<b>3. Hisoblash.</b> Javob uchun bazada SQL-soʻrov bajariladi. Raqamlar AI tomonidan oʻylab "
            "topilmaydi — faqat soʻrov natijasidan olinadi.\n\n"
            "<b>4. Tekshiruv.</b> Javobdagi har bir raqam soʻrov natijasi bilan avtomatik solishtiriladi. "
            "Tasdiqlanmagan raqam boʻlsa, javob yuborilmaydi va qayta tekshiriladi.\n\n"
            "<b>5. Shaffoflik.</b> Har javob ostidagi 🔎 blokda asos boʻlgan soʻrovlar koʻrsatiladi. "
            "Maʼlumotda javob boʻlmasa, bot buni ochiq aytadi.\n\n"
            "<i>Claude Sonnet 5.5 · Gemini · Groq · DuckDB · Python</i>"
        ),
        "btn_examples": "💡 Namuna savollar",
        "btn_about": "ℹ️ Bot haqida",
        "btn_new": "🆕 Yangi suhbat",
        "btn_web": "🌐 Veb-versiya",
        "placeholder": "Savolingizni yozing…",
        "new_done": "🆕 Yangi suhbat boshlandi. Oldingi savollar endi hisobga olinmaydi.",
        "web_text": "🌐 <b>Veb-versiya</b> — xuddi shu agent brauzerda, roʻyxatdan oʻtishsiz:",
        "web_open": "Ochish ↗",
        "only_text": "📝 Hozircha faqat matnli savollarni tushunaman. Savolingizni yozib yuboring.",
    },
    "ru": {
        "start": (
            "👋 <b>Здравствуйте!</b>\n\n"
            "Я — <b>UZEX AI-agent</b>. Отвечаю на вопросы о сделках биржевого реестра "
            "<b>строго по данным</b>.\n\n"
            "📊 <b>В базе:</b> 500 000 сделок (03.01.2022 – 30.10.2026), 6 616 контрактов, "
            "14 392 компании, 120 брокеров и ежедневный курс доллара.\n\n"
            "<b>О чём можно спросить:</b>\n"
            "• рейтинги — самые активные продавцы, покупатели, брокеры\n"
            "• суммы, объёмы и средние цены\n"
            "• по компании (название или ИНН), номеру контракта или сделки\n"
            "• в разрезе экспорта, статусов сделок, регионов и периодов\n\n"
            "🔎 Под каждым ответом видно, на каком запросе он основан.\n"
            "🚫 Если в данных ответа нет — честно об этом скажу.\n\n"
            "Пишите вопрос на <b>русском</b> или <b>узбекском</b> 👇"
        ),
        "examples_title": "💡 <b>Примеры вопросов</b> — нажмите, ответ придёт сразу:",
        "examples": [
            ("🏆 Топ-продавец 2025", "Кто из продавцов заключил больше всего сделок в 2025 году?"),
            ("🧪 Карбамид: сумма за 2024", "Какая общая сумма сделок по карбамиду в 2024 году?"),
            ("🌍 Экспорт: топ-регион", "В каком регионе больше всего экспортных сделок?"),
            ("❌ Аннулировано в 2026", "Сколько сделок было аннулировано в 2026 году?"),
            ("💵 Курс USD на 15.03.2025", "Какой был курс доллара 15 марта 2025 года?"),
            ("🌱 Хлопок: топ-покупатель 2025", "Кто купил больше всего хлопка-сырца в 2025 году?"),
        ],
        "about": (
            "ℹ️ <b>Как работает UZEX AI-agent</b>\n\n"
            "<b>1. Данные.</b> Реестр сделок биржи UZEX: 500 000 сделок (03.01.2022 – 30.10.2026), "
            "6 616 карточек контрактов, 14 392 компании, 120 брокеров, ежедневный курс доллара.\n\n"
            "<b>2. Понимание вопроса.</b> AI разбирает вопрос и находит в базе компанию, товар или брокера — "
            "с учётом кириллицы, латиницы и разных написаний.\n\n"
            "<b>3. Расчёт.</b> Для ответа выполняется SQL-запрос к базе. Цифры не придумываются моделью — "
            "они берутся только из результата запроса.\n\n"
            "<b>4. Проверка.</b> Каждое число в ответе автоматически сверяется с результатами запросов. "
            "Если число не подтверждено, ответ не отправляется и перепроверяется.\n\n"
            "<b>5. Прозрачность.</b> В блоке 🔎 под ответом видны запросы, на которых он основан. "
            "Если в данных ответа нет, бот прямо об этом сообщает.\n\n"
            "<i>Claude Sonnet 5.5 · Gemini · Groq · DuckDB · Python</i>"
        ),
        "btn_examples": "💡 Примеры вопросов",
        "btn_about": "ℹ️ О боте",
        "btn_new": "🆕 Новый диалог",
        "btn_web": "🌐 Веб-версия",
        "placeholder": "Задайте вопрос…",
        "new_done": "🆕 Начат новый диалог. Предыдущие вопросы больше не учитываются.",
        "web_text": "🌐 <b>Веб-версия</b> — тот же агент в браузере, без регистрации:",
        "web_open": "Открыть ↗",
        "only_text": "📝 Пока я понимаю только текстовые вопросы. Напишите, пожалуйста, вопрос текстом.",
    },
}

THINKING = {
    "uz": "⏳ Maʼlumotlar tekshirilmoqda… (odatda 5–20 soniya)",
    "uz_cyr": "⏳ Маълумотлар текширилмоқда… (одатда 5–20 сония)",
    "ru": "⏳ Проверяю данные… (обычно 5–20 секунд)",
}
BASIS = {
    "uz": "🔎 Asos: {n} ta SQL-soʻrov · {s} s",
    "uz_cyr": "🔎 Асос: {n} та SQL-сўров · {s} с",
    "ru": "🔎 Основание: SQL-запросов — {n} · {s} с",
}

# button label -> action (both languages)
ACTIONS = {}
for _l, _t in T.items():
    ACTIONS[_t["btn_examples"]] = "examples"
    ACTIONS[_t["btn_about"]] = "about"
    ACTIONS[_t["btn_new"]] = "new"
    ACTIONS[_t["btn_web"]] = "web"


def ui_lang(update: Update) -> str:
    u = update.effective_user
    return "ru" if u and (u.language_code or "").lower().startswith("ru") else "uz"


def menu(lang: str) -> ReplyKeyboardMarkup:
    t = T[lang]
    rows = [[KeyboardButton(t["btn_examples"]), KeyboardButton(t["btn_about"])],
            [KeyboardButton(t["btn_new"])] + ([KeyboardButton(t["btn_web"])] if PUBLIC_URL else [])]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True,
                               input_field_placeholder=t["placeholder"])


def examples_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"ex:{lang}:{i}")]
                                 for i, (label, _) in enumerate(T[lang]["examples"])])


def basis_block(res: agent.Result, lang: str, limit: int) -> str:
    ok = [q for q in res.queries if not q.get("error")]
    if not ok or limit < 200:
        return ""
    parts, used = [], 0
    for q in ok[-4:]:
        s = html.escape(q["sql"].strip())
        room = limit - used - 40
        if room <= 60:
            break
        if len(s) > room:
            s = s[:room] + "…"
        parts.append(f"{s}\n→ {q['rows']} rows")
        used += len(s) + 20
    head = BASIS[lang].format(n=len(ok), s=f"{res.seconds:.0f}")
    return f"\n\n<blockquote expandable><b>{head}</b>\n<code>" + "\n\n".join(parts) + "</code></blockquote>"


# ------------------------------------------------------------------ core: answer a question
async def answer_question(update: Update, ctx: ContextTypes.DEFAULT_TYPE, question: str, reply_to=None):
    chat_id = update.effective_chat.id
    qlang = agent.detect_lang(question)
    placeholder = await ctx.bot.send_message(chat_id, THINKING[qlang],
                                             reply_to_message_id=reply_to.message_id if reply_to else None)

    async def typing():
        while True:
            try:
                await ctx.bot.send_chat_action(chat_id, ChatAction.TYPING)
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(4.5)

    t = asyncio.create_task(typing())
    try:
        res = await agent.ask(question, await store.history(chat_id))
    except Exception:  # noqa: BLE001
        log.exception("agent failed")
        res = agent.Result(agent.NO_ANSWER[qlang], ok=False)
    finally:
        t.cancel()

    u = update.effective_user
    asyncio.create_task(store.save(chat_id, question, res.answer, res.ok, res.seconds, res.provider, res.queries,
                                   "tg", (u.username or u.full_name) if u else ""))
    body = html.escape(res.answer)[:3000]
    text = body + basis_block(res, qlang, limit=4000 - len(body) - 150)
    log.info("Q[%s]: %s | %.1fs %s | A: %s", chat_id, question[:200], res.seconds, res.provider,
             res.answer[:200].replace("\n", " "))
    try:
        await placeholder.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception:  # noqa: BLE001
        log.exception("edit failed, sending plain")
        await ctx.bot.send_message(chat_id, res.answer[:4000])


# ------------------------------------------------------------------ handlers
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ui_lang(update)
    await store.reset(update.effective_chat.id)
    await update.effective_message.reply_text(T[lang]["start"], parse_mode=ParseMode.HTML, reply_markup=menu(lang))
    await update.effective_message.reply_text(T[lang]["examples_title"], parse_mode=ParseMode.HTML,
                                              reply_markup=examples_kb(lang))


async def cmd_examples(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ui_lang(update)
    await update.effective_message.reply_text(T[lang]["examples_title"], parse_mode=ParseMode.HTML,
                                              reply_markup=examples_kb(lang))


async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ui_lang(update)
    await update.effective_message.reply_text(T[lang]["about"], parse_mode=ParseMode.HTML, reply_markup=menu(lang))


async def cmd_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ui_lang(update)
    await store.reset(update.effective_chat.id)
    await update.effective_message.reply_text(T[lang]["new_done"], reply_markup=menu(lang))


async def cmd_web(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ui_lang(update)
    if not PUBLIC_URL:
        return
    await update.effective_message.reply_text(
        T[lang]["web_text"], parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T[lang]["web_open"], url=PUBLIC_URL)]]))


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    q = (msg.text or "").strip()
    if not q:
        return
    action = ACTIONS.get(q)
    if action:
        return await {"examples": cmd_examples, "about": cmd_about, "new": cmd_new, "web": cmd_web}[action](update, ctx)
    await answer_question(update, ctx, q, reply_to=msg)


async def on_example(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, lang, i = query.data.split(":")
        question = T[lang]["examples"][int(i)][1]
    except Exception:  # noqa: BLE001
        return
    asked = await ctx.bot.send_message(update.effective_chat.id, f"❓ <b>{html.escape(question)}</b>",
                                       parse_mode=ParseMode.HTML)
    await answer_question(update, ctx, question, reply_to=asked)


async def on_other(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(T[ui_lang(update)]["only_text"])


def build_bot(token: str, public_url: str) -> Application:
    global PUBLIC_URL
    PUBLIC_URL = public_url
    app = Application.builder().token(token).concurrent_updates(True).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler("examples", cmd_examples))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("web", cmd_web))
    app.add_handler(CallbackQueryHandler(on_example, pattern=r"^ex:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND & ~filters.StatusUpdate.ALL, on_other))
    return app
