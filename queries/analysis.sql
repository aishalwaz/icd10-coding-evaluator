-- Ready-made analysis queries for the results database.
-- Run them all with:  python -m icd10_eval.query results.db
-- Or paste any single query into a SQLite tool such as DB Browser for SQLite.

-- name: Accuracy by specialty (weakest first)
SELECT specialty,
       COUNT(*)                                               AS cases,
       ROUND(100.0 * SUM(n_exact) / SUM(n_ai), 1)             AS precision_pct,
       ROUND(100.0 * SUM(n_exact) / SUM(n_reference), 1)      AS recall_pct,
       ROUND(100.0 * SUM(principal_correct) / COUNT(*), 1)    AS principal_dx_pct
FROM results
GROUP BY specialty
ORDER BY recall_pct ASC;

-- name: Most frequently missed codes
SELECT reference_code, COUNT(*) AS times_missed
FROM errors
WHERE error_type = 'missed'
GROUP BY reference_code
ORDER BY times_missed DESC, reference_code
LIMIT 10;

-- name: Specificity errors (right condition, wrong detail)
SELECT e.case_id, c.specialty, e.reference_code AS expected, e.ai_code AS ai_gave
FROM errors e
JOIN cases c ON c.case_id = e.case_id
WHERE e.error_type = 'specificity'
ORDER BY c.specialty, e.case_id;

-- name: Error types overall
SELECT error_type, COUNT(*) AS total
FROM errors
GROUP BY error_type
ORDER BY total DESC;

-- name: Cases with the wrong principal diagnosis
SELECT r.case_id, r.specialty,
       (SELECT code FROM codes WHERE case_id = r.case_id AND source = 'reference' AND position = 1) AS expected,
       (SELECT code FROM codes WHERE case_id = r.case_id AND source = 'ai' AND position = 1)        AS ai_gave
FROM results r
WHERE r.principal_correct = 0
ORDER BY r.case_id;
