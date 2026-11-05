# Test report

Every agent answer below was compared with the result of a hand-written SQL query over the same database.
Questions were asked in Russian, Uzbek Latin and Uzbek Cyrillic, including trap questions that have no answer in the data.

## Verified answers

| # | Question (language) | Correct value (manual SQL) | Agent | |
|---|---|---|---|---|
| 1 | 2025-yilda eng koʻp bitim tuzgan sotuvchi kim? (UZ) | "Kinen Energo" MChJ, INN 911688324 — 2 877 deals | same | ✅ |
| 2 | Какая общая сумма сделок по карбамиду в 2024 году? (RU) | 783 791 022 615 UZS; excl. cancelled 732 680 548 817 | same, 3 spelling variants included | ✅ |
| 3 | 2026-yilda nechta bitim bekor qilingan? (UZ) | 6 266 | same | ✅ |
| 4 | Qaysi viloyatda eksport bitimlari eng koʻp? (UZ) | Surxondaryo viloyati — 2 110 | same | ✅ |
| 5 | 104512-sonli shartnoma boʻyicha nechta bitim, jami summa? (UZ) | 370 deals, 212 893 444 352 UZS | same | ✅ |
| 6 | Расскажи о сделке номер 100003 (RU) | 03.01.2022, sunflower oil, 23 t, 505 863 932 UZS, Исполнен | same, all fields | ✅ |
| 7 | Какой брокер покупателя провёл больше всего сделок в Самаркандской области? (RU) | BK111 "Gucham Broker" MChJ — 876 | same | ✅ |
| 8 | Harayom Kimyo kompaniyasi sotuvchi sifatida nechta bitim tuzgan? (UZ, Latin name) | "ҲАРАЙЎМ КИМЁ" МЧЖ (Cyrillic in data), 10 608 | same | ✅ |
| 9 | 2025 йилда портландцементнинг ўртача нархи қанча? (UZ Cyrillic) | weighted avg 951 684,37 UZS/t | same, answered in Cyrillic | ✅ |
| 10 | Какой был курс доллара 15 марта 2025 года? (RU) | 12 589,97 | same | ✅ |
| 11 | 2023-yildagi eng katta bitim qaysi? (UZ) | deal 247890, 30 190 376 286 UZS | same | ✅ |
| 12 | Кто купил больше всего хлопка-сырца в 2025 году? (RU) | "Zoket Invest" OK — 103 545 907 kg | same | ✅ |
| 13 | 2024-yilning 3-choragida qaysi tovar boʻyicha eng koʻp summa? (UZ) | Пшеница продовольственная — 2 872 560 579 830 UZS | same | ✅ |
| 14 | Сколько сделок провёл брокер KEKUXO BROKER в 2025 как брокер продавца? (RU, Latin name) | "КЕКУХО БРОКЕР" МЧЖ (BK001) — 426 | same | ✅ |
| 15 | Eksport bitimlarining 2025-yildagi jami summasi necha dollar? (UZ) | 220 524 617,85 USD | same | ✅ |
| 16 | Средний рост цены от стартовой в англ. аукционах по бензину в 2026? (RU) | 3,21 % (4 298 deals) | same | ✅ |
| 17 | Qaysi xaridor eng koʻp pul sarflagan (barcha yillar)? (UZ) | "Zoket Invest" OK — 6 082 018 395 943,86 UZS | same | ✅ |
| 18 | Сколько контрактов зарегистрировано в 2023 году? (RU) | 1 062 (contracts table) | same (after fix) | ✅ |
| 19 | Сколько у Kinen Energo исполненных сделок в сентябре 2026? (RU) | 0 — the company's last deal is 30.09.2025 | same, with explanation | ✅ |

## Trap questions (no answer in the data)

| # | Question | Expected | Agent | |
|---|---|---|---|---|
| 20 | Какой номер телефона у компании Kinen Energo? | no phone numbers in the data | "В данных нет ответа…" + what fields exist | ✅ |
| 21 | 2021-yilda qancha bitim tuzilgan? | data starts 03.01.2022 | "Maʼlumotlarda bu savolga javob yoʻq" + available period | ✅ |
| 22 | Сколько сделок по золоту было в 2024 году? | no gold in the registry | "В данных нет ответа…" | ✅ |

## Issues found during testing and fixed

| Issue | Fix |
|---|---|
| A Russian question was answered in Uzbek | Required answer language is detected in code and passed explicitly with every question |
| Company names / statuses were transliterated | Rule: copy names, statuses and codes exactly as in the data |
| "Contracts registered" counted contracts that had deals (1 247) | Rule: contract questions use the `contracts` table → 1 062 |
| A side claim about cancelled deals was stated without a query | Code-level number check + rule: every extra claim needs its own query |
| Cancelled deals were silently excluded in a ranking | Rule: main figure over all deals, excluding-cancelled figure on a separate line |
| One spelling variant of a product was left out of an average | Rule: the main figure includes all spelling / word-order variants |

Response time in tests: 2–20 s per question (limit set to 80 s; the jury allows 90 s).
