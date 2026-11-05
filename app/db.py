"""Read-only DuckDB access used by the agent tools."""
import datetime as _dt
import decimal
import os
import re
import threading

import duckdb

from .textnorm import norm

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "uzex.duckdb"))
MAX_ROWS = 50
QUERY_TIMEOUT = 20  # seconds

_con = None
_lock = threading.Lock()


def con() -> duckdb.DuckDBPyConnection:
    global _con
    with _lock:
        if _con is None:
            _con = duckdb.connect(DB_PATH, read_only=True, config={"memory_limit": os.getenv("DUCKDB_MEMORY", "350MB"), "threads": int(os.getenv("DUCKDB_THREADS", "2"))})
        return _con


_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|create|alter|attach|detach|copy|export|import|install|load|pragma|set|call|checkpoint|vacuum)\b", re.I)


def _fmt(v):
    if v is None:
        return "NULL"
    if isinstance(v, float):
        if v.is_integer() and abs(v) < 1e15:
            return str(int(v))
        return f"{v:.4f}".rstrip("0").rstrip(".")
    if isinstance(v, decimal.Decimal):
        return _fmt(float(v))
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.isoformat()
    s = str(v)
    return s if len(s) <= 200 else s[:200] + "…"


def run_sql(sql: str) -> dict:
    """Execute a single read-only query. Returns {'columns', 'rows', 'total', 'text'} or {'error'}."""
    q = sql.strip().rstrip(";").strip()
    if not re.match(r"^(select|with|from|values|describe|summarize|show)\b", q, re.I):
        return {"error": "Only SELECT/WITH queries are allowed."}
    if ";" in q:
        return {"error": "Only one statement per call."}
    if _FORBIDDEN.search(re.sub(r"'[^']*'", "''", q)):
        return {"error": "Read-only: data modification / settings statements are not allowed."}
    cur = con().cursor()
    timer = threading.Timer(QUERY_TIMEOUT, cur.interrupt)
    timer.start()
    try:
        rel = cur.execute(q)
        cols = [d[0] for d in rel.description]
        rows = rel.fetchmany(MAX_ROWS + 1)
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "INTERRUPT" in msg.upper():
            msg = f"Query timed out after {QUERY_TIMEOUT}s; simplify it."
        return {"error": msg[:1500]}
    finally:
        timer.cancel()
        cur.close()
    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    lines = ["\t".join(cols)] + ["\t".join(_fmt(v) for v in r) for r in rows]
    text = "\n".join(lines)
    if not rows:
        text += "\n(0 rows — no matching data)"
    elif truncated:
        text += f"\n… (more than {MAX_ROWS} rows; showing first {MAX_ROWS}. Use aggregation/LIMIT.)"
    return {"columns": cols, "rows": rows, "text": text}


_stats_cache: dict | None = None


def stats() -> dict:
    """Dashboard numbers for the web app (computed once, cached)."""
    global _stats_cache
    if _stats_cache:
        return _stats_cache
    c = con().cursor()
    try:
        kpi = c.execute("""
            SELECT count(*), sum(amount_uzs), sum(amount_usd),
                   count(*) FILTER (WHERE contract_type='Экспортный'),
                   count(*) FILTER (WHERE status IN ('Исполнен','Исполнен(Частично)')),
                   min(deal_date), max(deal_date)
            FROM deals""").fetchone()
        years = c.execute("SELECT deal_year, count(*), sum(amount_uzs) FROM deals GROUP BY 1 ORDER BY 1").fetchall()
        months = c.execute("""SELECT strftime(date_trunc('month', deal_date), '%Y-%m'), count(*), sum(amount_uzs)
                              FROM deals GROUP BY 1 ORDER BY 1""").fetchall()
        cats = c.execute("""SELECT product_category, count(*), sum(amount_uzs) FROM deals
                            GROUP BY 1 ORDER BY 3 DESC""").fetchall()
        regions = c.execute("""SELECT region, count(*), sum(amount_uzs) FROM deals
                               GROUP BY 1 ORDER BY 2 DESC LIMIT 8""").fetchall()
        status = c.execute("SELECT status, count(*) FROM deals GROUP BY 1 ORDER BY 2 DESC").fetchall()
        n = {t: c.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("contracts", "participants", "brokers")}
    finally:
        c.close()
    _stats_cache = {
        "deals": kpi[0], "turnover_uzs": kpi[1], "turnover_usd": kpi[2], "export_deals": kpi[3],
        "executed_deals": kpi[4], "date_from": kpi[5].isoformat(), "date_to": kpi[6].isoformat(), **n,
        "by_year": [{"year": y, "deals": d, "uzs": s} for y, d, s in years],
        "by_month": [{"month": m, "deals": d, "uzs": s} for m, d, s in months],
        "by_category": [{"name": k, "deals": d, "uzs": s} for k, d, s in cats],
        "by_region": [{"name": k, "deals": d, "uzs": s} for k, d, s in regions],
        "by_status": [{"name": k, "deals": d} for k, d in status],
    }
    return _stats_cache


def find_entity(kind: str, query: str, limit: int = 12) -> dict:
    """Fuzzy lookup of companies / brokers / products across Cyrillic & Latin spellings."""
    qn = norm(query)
    if not qn:
        return {"error": "empty query"}
    cur = con().cursor()
    try:
        if kind == "company":
            sql = """
                WITH c AS (
                  SELECT p.inn, p.company_name, p.region, p.activity, p.role, p.name_norm,
                         greatest(jaro_winkler_similarity(p.name_norm, $qn),
                                  CASE WHEN p.name_norm LIKE '%' || $qn || '%' THEN 0.99 ELSE 0 END,
                                  CASE WHEN p.inn = $raw THEN 1.0 ELSE 0 END) AS score
                  FROM participants p)
                SELECT inn, company_name, region, activity, role, round(score, 3) AS score,
                       (SELECT count(*) FROM deals d WHERE d.seller_inn = c.inn) AS deals_as_seller,
                       (SELECT count(*) FROM deals d WHERE d.buyer_inn = c.inn) AS deals_as_buyer
                FROM c ORDER BY score DESC LIMIT $lim"""
        elif kind == "broker":
            sql = """
                SELECT broker_code, broker_name, broker_inn, region,
                       round(greatest(jaro_winkler_similarity(name_norm, $qn),
                                      CASE WHEN name_norm LIKE '%' || $qn || '%' THEN 0.99 ELSE 0 END,
                                      CASE WHEN upper(broker_code) = upper($raw) OR broker_inn = $raw THEN 1.0 ELSE 0 END), 3) AS score
                FROM brokers ORDER BY score DESC LIMIT $lim"""
        elif kind == "product":
            sql = """
                SELECT product_base, base_norm, tnved_code, product_category, unit, deals_count,
                       round(greatest(jaro_winkler_similarity(base_norm, $qn),
                                      CASE WHEN base_norm LIKE '%' || $qn || '%' THEN 0.99 ELSE 0 END,
                                      CASE WHEN tnved_code = $raw THEN 1.0 ELSE 0 END), 3) AS score
                FROM products ORDER BY score DESC, deals_count DESC LIMIT $lim"""
        else:
            return {"error": "kind must be company | broker | product"}
        rel = cur.execute(sql, {"qn": qn, "raw": query.strip(), "lim": limit})
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:1000]}
    finally:
        cur.close()
    lines = ["\t".join(cols)] + ["\t".join(_fmt(v) for v in r) for r in rows]
    note = f"normalized query: '{qn}'. score 1.0/0.99 = exact/substring match; < 0.9 is probably a DIFFERENT entity."
    return {"columns": cols, "rows": rows, "text": note + "\n" + "\n".join(lines)}
