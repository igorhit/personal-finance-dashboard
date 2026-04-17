import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Generator


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return url


@contextmanager
def get_conn() -> Generator[psycopg2.extensions.connection, None, None]:
    conn = psycopg2.connect(get_database_url(), cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id          SERIAL PRIMARY KEY,
                    description TEXT        NOT NULL,
                    amount      NUMERIC(12,2) NOT NULL CHECK (amount > 0),
                    category    TEXT        NOT NULL,
                    date        DATE        NOT NULL,
                    type        TEXT        NOT NULL CHECK (type IN ('income', 'expense')),
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_transactions_date     ON transactions (date);
                CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category);
                CREATE INDEX IF NOT EXISTS idx_transactions_type     ON transactions (type);
            """)
