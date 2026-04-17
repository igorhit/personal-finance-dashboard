from pathlib import Path
from typing import Any

from app.db.connection import get_conn

_SQL_DIR = Path(__file__).parent / "sql"


def _sql(name: str) -> str:
    return (_SQL_DIR / name).read_text(encoding="utf-8")


# ── Transactions ──────────────────────────────────────────────────────────────

def insert_transaction(
    description: str,
    amount: float,
    category: str,
    date: str,
    type_: str,
) -> dict[str, Any]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_sql("insert_transaction.sql"), (description, amount, category, date, type_))
            return dict(cur.fetchone())


def list_transactions(
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []

    if date_from:
        filters.append("date >= %s")
        params.append(date_from)
    if date_to:
        filters.append("date <= %s")
        params.append(date_to)
    if category:
        filters.append("category = %s")
        params.append(category)

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM transactions {where} ORDER BY date DESC, id DESC",
                params,
            )
            return [dict(row) for row in cur.fetchall()]


def delete_transaction(transaction_id: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_sql("delete_transaction.sql"), (transaction_id,))
            return cur.fetchone() is not None


def list_categories() -> list[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_sql("list_categories.sql"))
            return [row["category"] for row in cur.fetchall()]


# ── Reports ───────────────────────────────────────────────────────────────────

def get_summary(year: int, month: int) -> dict[str, Any]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_sql("get_summary.sql"), (year, month))
            row = cur.fetchone()
            return {
                "balance":       float(row["balance"]),
                "month_income":  float(row["month_income"]),
                "month_expense": float(row["month_expense"]),
            }


def get_expenses_by_category(year: int, month: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_sql("get_expenses_by_category.sql"), (year, month))
            return [
                {"category": row["category"], "total": float(row["total"]), "pct": float(row["pct"] or 0)}
                for row in cur.fetchall()
            ]


def get_monthly_balance_evolution(months: int = 12) -> list[dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_sql("get_monthly_balance_evolution.sql"), (months,))
            rows = cur.fetchall()
            return [
                {
                    "month":   row["month"].strftime("%Y-%m"),
                    "income":  float(row["income"]),
                    "expense": float(row["expense"]),
                    "net":     float(row["net"]),
                    "balance": float(row["balance"]),
                }
                for row in reversed(rows)
            ]
