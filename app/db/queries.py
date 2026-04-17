from typing import Any
import psycopg2.extras
from app.db.connection import get_conn


# ── Transactions ─────────────────────────────────────────────────────────────

def insert_transaction(
    description: str,
    amount: float,
    category: str,
    date: str,
    type_: str,
) -> dict[str, Any]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (description, amount, category, date, type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (description, amount, category, date, type_),
            )
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
            cur.execute(
                "DELETE FROM transactions WHERE id = %s RETURNING id",
                (transaction_id,),
            )
            return cur.fetchone() is not None


def list_categories() -> list[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT category FROM transactions ORDER BY category")
            return [row["category"] for row in cur.fetchall()]


# ── Reports ───────────────────────────────────────────────────────────────────

def get_summary(year: int, month: int) -> dict[str, Any]:
    """
    Returns current balance (all time) plus income/expense totals for the
    requested month.  Uses a single CTE pass to avoid multiple round-trips.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH all_time AS (
                    SELECT
                        COALESCE(SUM(CASE WHEN type = 'income'  THEN amount ELSE 0 END), 0) AS total_income_all,
                        COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS total_expense_all
                    FROM transactions
                ),
                this_month AS (
                    SELECT
                        COALESCE(SUM(CASE WHEN type = 'income'  THEN amount ELSE 0 END), 0) AS month_income,
                        COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS month_expense
                    FROM transactions
                    WHERE EXTRACT(YEAR  FROM date) = %s
                      AND EXTRACT(MONTH FROM date) = %s
                )
                SELECT
                    (a.total_income_all - a.total_expense_all) AS balance,
                    m.month_income,
                    m.month_expense
                FROM all_time a, this_month m
                """,
                (year, month),
            )
            row = cur.fetchone()
            return {
                "balance":       float(row["balance"]),
                "month_income":  float(row["month_income"]),
                "month_expense": float(row["month_expense"]),
            }


def get_expenses_by_category(year: int, month: int) -> list[dict[str, Any]]:
    """
    Expense breakdown by category for a given month, sorted descending,
    with percentage share computed via window function.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH monthly_expenses AS (
                    SELECT
                        category,
                        SUM(amount) AS total
                    FROM transactions
                    WHERE type = 'expense'
                      AND EXTRACT(YEAR  FROM date) = %s
                      AND EXTRACT(MONTH FROM date) = %s
                    GROUP BY category
                ),
                totals AS (
                    SELECT SUM(total) AS grand_total FROM monthly_expenses
                )
                SELECT
                    me.category,
                    me.total,
                    ROUND(me.total * 100.0 / NULLIF(t.grand_total, 0), 1) AS pct
                FROM monthly_expenses me, totals t
                ORDER BY me.total DESC
                """,
                (year, month),
            )
            return [
                {"category": row["category"], "total": float(row["total"]), "pct": float(row["pct"] or 0)}
                for row in cur.fetchall()
            ]


def get_monthly_balance_evolution(months: int = 12) -> list[dict[str, Any]]:
    """
    Running balance month by month for the last N months.
    Uses a CTE with a cumulative window sum so the SQL does all the math.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH monthly_net AS (
                    SELECT
                        DATE_TRUNC('month', date)::DATE AS month,
                        SUM(CASE WHEN type = 'income'  THEN  amount ELSE 0 END) AS income,
                        SUM(CASE WHEN type = 'expense' THEN  amount ELSE 0 END) AS expense,
                        SUM(CASE WHEN type = 'income'  THEN  amount
                                 WHEN type = 'expense' THEN -amount ELSE 0 END) AS net
                    FROM transactions
                    GROUP BY DATE_TRUNC('month', date)
                    ORDER BY month
                ),
                running AS (
                    SELECT
                        month,
                        income,
                        expense,
                        net,
                        SUM(net) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS balance
                    FROM monthly_net
                )
                SELECT *
                FROM running
                ORDER BY month DESC
                LIMIT %s
                """,
                (months,),
            )
            rows = cur.fetchall()
            # Return chronological order for charting
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
