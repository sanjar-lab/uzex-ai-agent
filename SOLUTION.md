# UZEX AI-agent — yechim tavsifi

**Prototip:** Telegram-bot + veb-chat (bitta servis). Roʻyxatdan oʻtishsiz ishlaydi, savollarni oʻzbek (lotin/kirill) va rus tilida tushunadi, savol tilida javob beradi.

## Arxitektura
1. **Maʼlumotlar qatlami — DuckDB.** 5 ta `deals_*.csv`, `contracts`, `participants`, `brokers`, `usd_rates` bitta DuckDB bazaga yuklanadi (`build_db.py`, ~6 soniya). Raqamlar (`304 547 938.4`), sanalar (`ДД.ММ.ГГГГ`) toʻgʻri turlarga oʻtkaziladi. README dagi formulalar oldindan hisoblanadi: `volume = Количество × Лот`, `unit_price = Сумма ÷ volume`, valyuta (shartnomadan), `amount_uzs` (USD bitimlar shu kungi kurs boʻyicha soʻmga), `amount_usd`, sotuvchi/xaridor/broker nomlari.
2. **Nomlarni moslashtirish.** Kompaniya, broker va tovar nomlari kirill/lotin/apostrof farqlaridan qatʼi nazar transliteratsiya qilinib normallashtiriladi (`"ҚОПУР БРОКЕР" МЧЖ` → `qopur broker`). `find_entity` vositasi fuzzy-qidiruv (Jaro-Winkler) bilan nomni STIR / broker kodi / TN VED kodiga bogʻlaydi. Bir xil tovarning turlicha yozilishi (`Хлопок сырец` / `Хлопок-сырец` / `ХЛОПОК-СЫРЕЦ`) TN VED kodi va normallashtirilgan nom orqali birlashtiriladi.
3. **AI-agent (text-to-SQL, tool calling).** LLM savolni tahlil qiladi, `find_entity` va `run_sql` vositalarini chaqiradi, natijani tekshiradi va faqat olingan qatorlar asosida javob yozadi. Har bir savolga 10 tagacha qadam, 80 soniyalik limit (komissiya 90 s beradi).
4. **LLM:** Gemini 2.5 Flash (bir nechta kalit, round-robin), zaxira — Groq (gpt-oss-120b). OpenAI-compatible API orqali; limit/xato boʻlsa avtomatik keyingi provayderga oʻtadi.

## Javoblar qanday tekshiriladi / gallyutsinatsiyaga qarshi
- Tizim promptida qatʼiy qoidalar: har bir raqam, kompaniya, kod faqat shu suhbatdagi SQL natijasidan olinadi; maʼlumot boʻlmasa — "Maʼlumotlarda bu savolga javob yoʻq" / "В данных нет ответа".
- **Kod darajasidagi himoya:** agar model maʼlumotni tekshirmasdan (birorta muvaffaqiyatli SQL soʻrovsiz) javob bersa, javob qabul qilinmaydi va model avval maʼlumotni tekshirishga majburlanadi.
- SQL faqat oʻqish rejimida (`read_only` ulanish, faqat SELECT/WITH, 20 s timeout, 50 qator limiti).
- **Shaffoflik:** har bir javob ostida u asoslangan SQL soʻrovlar va qaytgan qatorlar soni koʻrsatiladi (Telegramda yigʻiladigan blok, veb-chatda "Asos / Основание").
- Pul summalarini turli valyutalarda qoʻshib yubormaslik, hajmni turli oʻlchov birliklarida qoʻshmaslik, bekor qilingan bitimlarni alohida koʻrsatish qoidalari promptda belgilangan.
- Test toʻplami: RU/UZ savollar (reyting, summa, oʻrtacha narx, STIR boʻyicha, broker, eksport, holatlar, maʼlumotda yoʻq savollar) qoʻlda SQL bilan solishtirilib tekshirildi.

## Texnologiyalar
Python 3.11 · DuckDB · FastAPI + Uvicorn · python-telegram-bot 21 (webhook) · OpenAI-compatible SDK → Google Gemini / Groq · Render (hosting).
