"""Turn results into readable text, Markdown or JSON."""

import json
from dataclasses import asdict

_COLUMNS = [
    ("Cases", "cases"), ("Precision %", "precision"), ("Recall %", "recall"),
    ("F1 %", "f1"), ("Category recall %", "category_recall"),
    ("Principal dx %", "principal_accuracy"), ("Fully correct cases %", "case_accuracy"),
]


def _error_lines(results):
    """One readable line per coding error, for the error log."""
    lines = []
    for r in results:
        for ref, ai in r.specificity_errors:
            lines.append(f"{r.case_id}  specificity  expected {ref}, AI gave {ai}")
        for code in r.missed:
            lines.append(f"{r.case_id}  missed       {code}")
        for code in r.extra:
            lines.append(f"{r.case_id}  extra        {code}")
        if r.sequencing_error:
            lines.append(f"{r.case_id}  sequencing   {r.principal_ai} listed first; "
                         f"principal diagnosis is {r.principal_reference}")
        for code in r.invalid_format:
            lines.append(f"{r.case_id}  format       {code} is not a valid ICD-10-CM format")
    return lines


def to_text(overall, specialties, results) -> str:
    out = [
        "ICD-10-CM CODING ACCURACY",
        f"Cases: {overall.cases}   Reference codes: {overall.reference_codes}   "
        f"AI codes: {overall.ai_codes}",
        "",
        f"Exact matches:        {overall.exact_matches}",
        f"Specificity errors:   {overall.specificity_errors}  (right category, wrong detail)",
        f"Missed codes:         {overall.missed}",
        f"Extra codes:          {overall.extra}",
        "",
        f"Precision:            {overall.precision}%",
        f"Recall:               {overall.recall}%",
        f"F1 score:             {overall.f1}%",
        f"Category recall:      {overall.category_recall}%",
        f"Principal diagnosis:  {overall.principal_accuracy}%",
        f"Fully correct cases:  {overall.case_accuracy}%",
        "",
        "BY SPECIALTY (weakest first)",
        f"{'Specialty':<22}{'Cases':>6}{'Prec %':>9}{'Rec %':>8}{'F1 %':>8}",
    ]
    for s in specialties:
        out.append(f"{s.label:<22}{s.cases:>6}{s.precision:>9}{s.recall:>8}{s.f1:>8}")
    errors = _error_lines(results)
    out += ["", f"ERROR LOG ({len(errors)})"] + (errors or ["No errors."])
    return "\n".join(out)


def to_markdown(overall, specialties, results) -> str:
    header = "| Group | " + " | ".join(name for name, _ in _COLUMNS) + " |"
    divider = "|---" * (len(_COLUMNS) + 1) + "|"
    rows = [header, divider]
    for s in [overall] + specialties:
        values = " | ".join(str(getattr(s, attr)) for _, attr in _COLUMNS)
        rows.append(f"| {s.label} | {values} |")
    errors = _error_lines(results)
    return "\n".join(
        ["# ICD-10-CM Coding Accuracy", ""] + rows
        + ["", "## Error log", ""] + [f"- {e}" for e in errors or ["No errors."]]
    )


def to_json(overall, specialties, results) -> str:
    return json.dumps({
        "overall": asdict(overall),
        "by_specialty": [asdict(s) for s in specialties],
        "cases": [asdict(r) | {"fully_correct": r.fully_correct} for r in results],
    }, indent=2)
