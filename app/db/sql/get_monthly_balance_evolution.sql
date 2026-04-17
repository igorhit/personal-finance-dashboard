-- Monthly balance evolution for the last N months.
-- monthly_net aggregates income, expense and net per month.
-- running uses a cumulative window function (SUM OVER) to compute the
-- running balance without application-side iteration.
WITH monthly_net AS (
    SELECT
        DATE_TRUNC('month', date)::DATE                                       AS month,
        SUM(CASE WHEN type = 'income'  THEN  amount ELSE 0 END)              AS income,
        SUM(CASE WHEN type = 'expense' THEN  amount ELSE 0 END)              AS expense,
        SUM(CASE WHEN type = 'income'  THEN  amount
                 WHEN type = 'expense' THEN -amount ELSE 0 END)              AS net
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
        SUM(net) OVER (
            ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS balance
    FROM monthly_net
)
SELECT *
FROM running
ORDER BY month DESC
LIMIT %s;
