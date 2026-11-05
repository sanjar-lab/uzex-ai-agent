"""Build data/uzex.duckdb from the raw CSV files in uzex_spot_data/.

Usage: python build_db.py [csv_dir] [out_path]
"""
import os
import sys
import time

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.textnorm import norm  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else "uzex_spot_data"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join("data", "uzex.duckdb")


def num(col: str) -> str:
    """'304 547 938.4' -> 304547938.4 (handles normal and non-breaking spaces)."""
    return f"TRY_CAST(NULLIF(regexp_replace(\"{col}\", '[^0-9.\\-]', '', 'g'), '') AS DOUBLE)"


def dt(col: str) -> str:
    return f"TRY_STRPTIME(NULLIF(\"{col}\", ''), '%d.%m.%Y')::DATE"


def csv(name: str) -> str:
    p = os.path.join(SRC, name).replace("\\", "/")
    return f"read_csv('{p}', all_varchar=true, header=true, quote='\"', escape='\"')"


def main():
    t0 = time.time()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    con = duckdb.connect(OUT)

    # ---------- reference tables ----------
    con.execute(f"""
        CREATE TABLE usd_rates AS
        SELECT {dt('Дата')} AS rate_date, {num('Курс')} AS usd_rate FROM {csv('usd_rates.csv')}
    """)

    con.execute(f"""
        CREATE TABLE brokers AS
        SELECT "Код брокера" AS broker_code, "Наименование" AS broker_name, "ИНН" AS broker_inn, "Регион" AS region
        FROM {csv('brokers.csv')}
    """)

    con.execute(f"""
        CREATE TABLE participants AS
        SELECT "ИНН" AS inn, "Наименование" AS company_name, "Регион" AS region,
               "Вид деятельности" AS activity, "Роль" AS role, "Плательщик НДС" AS vat_payer
        FROM {csv('participants.csv')}
    """)

    con.execute(f"""
        CREATE TABLE contracts AS
        SELECT TRY_CAST("Номер контракта" AS BIGINT) AS contract_id,
               "Наименование продукта" AS product_base,
               "Марка товара" AS brand, "Размер товара" AS size, "Сорт товара" AS grade,
               "Тип товара" AS ptype, "Класс товара" AS pclass,
               "Код ТН ВЭД" AS tnved_code, "Группа товара" AS product_group,
               "Категория товара" AS product_category, "Отрасль промышленности" AS industry,
               "Единица измерения" AS unit, {num('Лот')} AS lot, "Валюта" AS currency,
               {num('Базисная цена')} AS base_price, "Сумма залога" AS deposit_pct,
               "Базис поставки" AS delivery_basis, "Регион" AS region, "Адрес склада" AS warehouse_address,
               "Тип торгов" AS trade_type, "Тип контракта" AS contract_type, "Форма контракта" AS contract_form,
               TRY_CAST("Срок оплаты" AS INTEGER) AS payment_term_days,
               TRY_CAST("Срок поставки" AS INTEGER) AS delivery_term_days,
               "Упаковка" AS packaging, "ИНН продавца" AS seller_inn,
               {dt('Дата регистрации')} AS registered_date, {dt('Действует до')} AS valid_until
        FROM {csv('contracts.csv')}
    """)

    # ---------- deals (raw) ----------
    files = sorted(f for f in os.listdir(SRC) if f.startswith("deals_") and f.endswith(".csv"))
    union = " UNION ALL ".join(f"SELECT * FROM {csv(f)}" for f in files)
    con.execute(f"""
        CREATE TEMP TABLE deals_raw AS
        SELECT TRY_CAST("Номер сделки" AS BIGINT) AS deal_id,
               {dt('Дата сделки')} AS deal_date, "Время сделки" AS deal_time,
               "Тип торгов" AS trade_type, {num('Количество')} AS quantity,
               {num('Сумма сделки')} AS amount, {num('Стартовая цена')} AS start_price,
               TRY_CAST("Номер контракта" AS BIGINT) AS contract_id,
               "Наименование товара" AS product_name, {num('Лот')} AS lot,
               "Единица измерения" AS unit, "Регион" AS region,
               "Тип контракта" AS contract_type, "Форма контракта" AS contract_form,
               "Состояние сделки" AS status, "ИНН продавца" AS seller_inn, "ИНН покупателя" AS buyer_inn,
               "Брокер продавца" AS seller_broker, "Брокер покупателя" AS buyer_broker,
               {dt('Дата оплаты')} AS payment_date, {dt('Дата поставки')} AS delivery_date,
               {num('Поставлено')} AS delivered_lots
        FROM ({union})
    """)

    # ---------- wide deals table (everything the LLM usually needs, no joins) ----------
    con.execute("""
        CREATE TABLE deals AS
        SELECT d.*,
               year(d.deal_date) AS deal_year, month(d.deal_date) AS deal_month,
               d.quantity * d.lot AS volume,
               d.amount / NULLIF(d.quantity * d.lot, 0) AS unit_price,
               c.currency,
               r.usd_rate,
               CASE WHEN c.currency = 'Доллар США' THEN d.amount * r.usd_rate ELSE d.amount END AS amount_uzs,
               CASE WHEN c.currency = 'Доллар США' THEN d.amount ELSE d.amount / r.usd_rate END AS amount_usd,
               c.product_base, c.product_group, c.product_category, c.industry, c.tnved_code,
               ps.company_name AS seller_name, pb.company_name AS buyer_name,
               bs.broker_name AS seller_broker_name, bb.broker_name AS buyer_broker_name
        FROM deals_raw d
        LEFT JOIN contracts c ON c.contract_id = d.contract_id
        LEFT JOIN usd_rates r ON r.rate_date = d.deal_date
        LEFT JOIN participants ps ON ps.inn = d.seller_inn
        LEFT JOIN participants pb ON pb.inn = d.buyer_inn
        LEFT JOIN brokers bs ON bs.broker_code = d.seller_broker
        LEFT JOIN brokers bb ON bb.broker_code = d.buyer_broker
        ORDER BY d.deal_id
    """)

    # ---------- normalized (transliterated) search keys ----------
    def add_norm(table: str, key: str, src: str, extra_src: str | None = None):
        rows = con.execute(f"SELECT DISTINCT {src} FROM {table} WHERE {src} IS NOT NULL").fetchall()
        con.execute(f"CREATE TEMP TABLE _n (v VARCHAR, n VARCHAR)")
        con.executemany("INSERT INTO _n VALUES (?, ?)", [(r[0], norm(r[0])) for r in rows])
        con.execute(f"ALTER TABLE {table} ADD COLUMN {key} VARCHAR")
        con.execute(f"UPDATE {table} t SET {key} = _n.n FROM _n WHERE t.{src} = _n.v")
        con.execute("DROP TABLE _n")

    # products dictionary for fuzzy lookup
    con.execute("""
        CREATE TABLE products AS
        SELECT product_base, tnved_code, product_category, industry, unit,
               count(*) AS deals_count, count(DISTINCT product_name) AS name_variants
        FROM deals GROUP BY ALL
    """)

    add_norm("participants", "name_norm", "company_name")
    add_norm("brokers", "name_norm", "broker_name")
    add_norm("contracts", "product_norm", "product_base")
    add_norm("deals", "product_norm", "product_name")
    add_norm("products", "base_norm", "product_base")

    con.execute("DROP TABLE deals_raw")
    con.execute("CHECKPOINT")
    n = con.execute("SELECT count(*), min(deal_date), max(deal_date), count(currency), count(usd_rate) FROM deals").fetchone()
    print("deals:", n)
    for t in ["contracts", "participants", "brokers", "usd_rates", "products"]:
        print(t, con.execute(f"SELECT count(*) FROM {t}").fetchone()[0])
    con.close()
    print(f"built {OUT} in {time.time() - t0:.1f}s, size {os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
