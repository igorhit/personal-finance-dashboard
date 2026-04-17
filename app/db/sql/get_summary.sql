-- Returns the all-time balance alongside income/expense totals for a given month.
-- Two CTEs avoid multiple round-trips: all_time computes the running balance,
-- this_month scopes totals to the requested year/month.
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
FROM all_time a, this_month m;
