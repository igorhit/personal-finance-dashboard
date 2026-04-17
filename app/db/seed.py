import random
from datetime import date, timedelta
from app.db.connection import get_conn

_INCOME_SOURCES = [
    ("Salário",         "Salário",      3_800),
    ("Freelance",       "Freelance",      900),
    ("Dividendos",      "Investimentos",  250),
]

_EXPENSE_TEMPLATES = [
    ("Aluguel",          "Moradia",       1_400),
    ("Supermercado",     "Alimentação",     600),
    ("Streaming",        "Lazer",            55),
    ("Academia",         "Saúde",            99),
    ("Plano de saúde",   "Saúde",           320),
    ("Combustível",      "Transporte",      280),
    ("Restaurante",      "Alimentação",     180),
    ("Farmácia",         "Saúde",            90),
    ("Roupas",           "Vestuário",       150),
    ("Energia elétrica", "Moradia",         130),
    ("Internet",         "Moradia",          99),
    ("Uber",             "Transporte",       80),
    ("Cinema/Teatro",    "Lazer",            60),
    ("Livros",           "Educação",         70),
    ("Curso online",     "Educação",        150),
]


def _already_seeded(cur) -> bool:
    cur.execute("SELECT COUNT(*) AS n FROM transactions")
    return cur.fetchone()["n"] > 0


def run_seed() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if _already_seeded(cur):
                return

            today = date.today()
            rows: list[tuple] = []

            for month_offset in range(11, -1, -1):
                # First day of the target month
                first = (today.replace(day=1) - timedelta(days=month_offset * 28)).replace(day=1)
                # Last day of the target month
                next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
                last = next_month - timedelta(days=1)

                def rand_date() -> date:
                    delta = (last - first).days
                    return first + timedelta(days=random.randint(0, delta))

                # Income entries
                for desc, cat, base in _INCOME_SOURCES:
                    jitter = random.uniform(0.95, 1.05)
                    rows.append((desc, round(base * jitter, 2), cat, rand_date(), "income"))

                # Expense entries — all templates + a few random extras
                for desc, cat, base in _EXPENSE_TEMPLATES:
                    jitter = random.uniform(0.85, 1.15)
                    rows.append((desc, round(base * jitter, 2), cat, rand_date(), "expense"))

                # 2–4 random small expenses per month
                for _ in range(random.randint(2, 4)):
                    extra_desc, extra_cat, extra_base = random.choice(_EXPENSE_TEMPLATES)
                    rows.append((
                        f"{extra_desc} (extra)",
                        round(extra_base * random.uniform(0.3, 0.7), 2),
                        extra_cat,
                        rand_date(),
                        "expense",
                    ))

            cur.executemany(
                "INSERT INTO transactions (description, amount, category, date, type) VALUES (%s,%s,%s,%s,%s)",
                rows,
            )
            print(f"[seed] Inserted {len(rows)} transactions.")
