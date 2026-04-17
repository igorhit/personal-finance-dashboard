CREATE TABLE IF NOT EXISTS transactions (
    id          SERIAL PRIMARY KEY,
    description TEXT          NOT NULL,
    amount      NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    category    TEXT          NOT NULL,
    date        DATE          NOT NULL,
    type        TEXT          NOT NULL CHECK (type IN ('income', 'expense')),
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_date     ON transactions (date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category);
CREATE INDEX IF NOT EXISTS idx_transactions_type     ON transactions (type);
