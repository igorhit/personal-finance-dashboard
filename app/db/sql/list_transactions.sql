-- Filters are appended dynamically in queries.py (date_from, date_to, category).
-- Base query — WHERE clause and ORDER are added at runtime.
SELECT *
FROM transactions
ORDER BY date DESC, id DESC;
