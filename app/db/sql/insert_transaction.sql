INSERT INTO transactions (description, amount, category, date, type)
VALUES (%s, %s, %s, %s, %s)
RETURNING *;
