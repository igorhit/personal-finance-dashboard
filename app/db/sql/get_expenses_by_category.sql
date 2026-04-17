-- Expense breakdown by category for a given month.
-- monthly_expenses aggregates per category; totals computes the grand total
-- so each row can carry its percentage share without a subquery per row.
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
    SELECT SUM(total) AS grand_total
    FROM monthly_expenses
)
SELECT
    me.category,
    me.total,
    ROUND(me.total * 100.0 / NULLIF(t.grand_total, 0), 1) AS pct
FROM monthly_expenses me, totals t
ORDER BY me.total DESC;
