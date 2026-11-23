"""Run the ready-made SQL analysis queries against a results database.

  python -m icd10_eval.query results.db

Each query in queries/analysis.sql starts with a "-- name:" comment line;
this script runs them one by one and prints each result as a table.
"""

import sqlite3
import sys
from pathlib import Path

QUERY_FILE = Path(__file__).resolve().parent.parent / "queries" / "analysis.sql"


def load_queries(path=QUERY_FILE) -> list:
    """Split the SQL file into (name, sql) pairs using the '-- name:' markers."""
    queries, name, lines = [], None, []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("-- name:"):
            if name:
                queries.append((name, "\n".join(lines).strip()))
            name, lines = line[len("-- name:"):].strip(), []
        elif name:
            lines.append(line)
    if name:
        queries.append((name, "\n".join(lines).strip()))
    return queries


def print_table(cursor) -> None:
    """Print query results as simple aligned columns."""
    headers = [d[0] for d in cursor.description]
    rows = [[("" if v is None else str(v)) for v in row] for row in cursor.fetchall()]
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
              for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows or [["(no rows)"] + [""] * (len(headers) - 1)]:
        print("  ".join(v.ljust(w) for v, w in zip(row, widths)))


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: python -m icd10_eval.query RESULTS.db", file=sys.stderr)
        return 2
    con = sqlite3.connect(argv[0])
    try:
        for name, sql in load_queries():
            print(f"\n== {name} ==")
            print_table(con.execute(sql))
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
