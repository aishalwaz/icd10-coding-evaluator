"""Save cases and results to a SQLite database for analysis with SQL.

SQLite is a database stored in a single file. Python includes it, so
nothing extra needs installing. Tables created:

  cases    one row per case
  codes    every reference and AI code, one row per code
  results  one row per case with its scores
  errors   one row per coding error (missed, extra or specificity)
"""

import sqlite3

SCHEMA = """
DROP TABLE IF EXISTS errors;
DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS codes;
DROP TABLE IF EXISTS cases;

CREATE TABLE cases (
    case_id   TEXT PRIMARY KEY,
    specialty TEXT NOT NULL,
    summary   TEXT
);

CREATE TABLE codes (
    case_id  TEXT REFERENCES cases(case_id),
    source   TEXT CHECK (source IN ('reference', 'ai')),
    position INTEGER,          -- 1 = principal diagnosis
    code     TEXT NOT NULL,
    category TEXT NOT NULL     -- first 3 characters, e.g. E11
);

CREATE TABLE results (
    case_id            TEXT PRIMARY KEY REFERENCES cases(case_id),
    specialty          TEXT,
    n_reference        INTEGER,
    n_ai               INTEGER,
    n_exact            INTEGER,
    n_specificity      INTEGER,
    n_missed           INTEGER,
    n_extra            INTEGER,
    fully_correct      INTEGER,  -- 1 = yes, 0 = no
    principal_correct  INTEGER
);

CREATE TABLE errors (
    case_id        TEXT REFERENCES cases(case_id),
    error_type     TEXT CHECK (error_type IN ('missed', 'extra', 'specificity')),
    reference_code TEXT,
    ai_code        TEXT
);
"""


def save(db_path, cases, results) -> None:
    """Write all cases and results to db_path (any existing tables are replaced)."""
    con = sqlite3.connect(db_path)
    try:
        con.executescript(SCHEMA)

        for case in cases:
            con.execute("INSERT INTO cases VALUES (?, ?, ?)",
                        (case.case_id, case.specialty, case.summary))
            for source, codes in (("reference", case.reference_codes), ("ai", case.ai_codes)):
                for position, code in enumerate(codes, start=1):
                    con.execute("INSERT INTO codes VALUES (?, ?, ?, ?, ?)",
                                (case.case_id, source, position, code, code[:3]))

        for r in results:
            con.execute(
                "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (r.case_id, r.specialty, r.n_reference, r.n_ai, len(r.exact),
                 len(r.specificity_errors), len(r.missed), len(r.extra),
                 int(r.fully_correct), int(r.principal_correct)),
            )
            rows = [(r.case_id, "missed", code, None) for code in r.missed]
            rows += [(r.case_id, "extra", None, code) for code in r.extra]
            rows += [(r.case_id, "specificity", ref, ai) for ref, ai in r.specificity_errors]
            con.executemany("INSERT INTO errors VALUES (?, ?, ?, ?)", rows)

        con.commit()
    finally:
        con.close()
