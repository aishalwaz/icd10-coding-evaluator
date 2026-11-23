"""Command-line interface.

Examples:
  python -m icd10_eval.cli examples/cases.csv
  python -m icd10_eval.cli examples/cases.csv --format markdown
  python -m icd10_eval.cli examples/cases.csv --db results.db
"""

import argparse
import sys

from . import database, report
from .data import load_cases
from .metrics import by_specialty, evaluate_case, summarise

FORMATTERS = {"text": report.to_text, "markdown": report.to_markdown, "json": report.to_json}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure how accurately an AI model assigns ICD-10-CM codes.")
    parser.add_argument("cases", help="CSV file of cases with reference and AI codes")
    parser.add_argument("--format", choices=FORMATTERS, default="text", help="output format")
    parser.add_argument("--db", help="also save everything to this SQLite database file")
    args = parser.parse_args(argv)

    try:
        cases = load_cases(args.cases)
    except (OSError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    results = [evaluate_case(c) for c in cases]
    overall = summarise(results)
    print(FORMATTERS[args.format](overall, by_specialty(results), results))

    if args.db:
        database.save(args.db, cases, results)
        print(f"\nSaved to {args.db}. Try: python -m icd10_eval.query {args.db}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
