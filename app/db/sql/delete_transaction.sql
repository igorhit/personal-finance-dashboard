DELETE FROM transactions
WHERE id = %s
RETURNING id;
