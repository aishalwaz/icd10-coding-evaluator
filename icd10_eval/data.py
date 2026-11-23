"""Load clinical cases from a CSV file.

Expected columns (one row per case):
  case_id          unique ID, e.g. C001
  specialty        e.g. Cardiology
  case_summary     short synthetic case description
  reference_codes  expert codes, separated by ";"  (principal diagnosis first)
  ai_codes         the AI model's codes, separated by ";" (principal first)
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path

from .codes import normalise_code

REQUIRED_COLUMNS = {"case_id", "specialty", "case_summary", "reference_codes", "ai_codes"}


@dataclass
class Case:
    case_id: str
    specialty: str
    summary: str
    reference_codes: list = field(default_factory=list)
    ai_codes: list = field(default_factory=list)


def split_codes(cell: str) -> list:
    """Turn "I10; E11.9" into ["I10", "E11.9"], keeping order and dropping duplicates."""
    codes = []
    for part in (cell or "").split(";"):
        if part.strip():
            code = normalise_code(part)
            if code not in codes:
                codes.append(code)
    return codes


def load_cases(path) -> list:
    """Read the CSV file and return a list of Case objects.

    Raises ValueError if columns are missing, a case ID repeats, or a case
    has no reference codes (it could not be scored fairly).
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name}: missing column(s): {', '.join(sorted(missing))}")

        cases, seen = [], set()
        for row in reader:
            case_id = row["case_id"].strip()
            if case_id in seen:
                raise ValueError(f"Duplicate case_id: {case_id}")
            seen.add(case_id)

            reference = split_codes(row["reference_codes"])
            if not reference:
                raise ValueError(f"Case {case_id} has no reference codes")

            cases.append(Case(
                case_id=case_id,
                specialty=row["specialty"].strip(),
                summary=row["case_summary"].strip(),
                reference_codes=reference,
                ai_codes=split_codes(row["ai_codes"]),
            ))
    return cases
