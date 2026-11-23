"""Tests for the ICD-10-CM evaluator. Run with:  python -m pytest"""

import json
import sqlite3
from pathlib import Path

import pytest

from icd10_eval import Case, category, evaluate_case, is_valid, load_cases, normalise_code, summarise
from icd10_eval.cli import main
from icd10_eval.metrics import by_specialty
from icd10_eval.query import load_queries
from icd10_eval import database

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "examples" / "cases.csv"


def case(reference, ai, specialty="Test"):
    return Case("T1", specialty, "summary", reference, ai)


# --- Code handling -------------------------------------------------------

def test_normalise_adds_dot_and_uppercases():
    assert normalise_code(" e1165 ") == "E11.65"
    assert normalise_code("i10") == "I10"


def test_format_validation():
    assert is_valid("S72.001A") and is_valid("I10") and is_valid("F32.A")
    assert not is_valid("11.65") and not is_valid("E11.12345")


def test_category():
    assert category("E11.65") == "E11"


# --- Scoring one case ----------------------------------------------------

def test_perfect_case():
    r = evaluate_case(case(["I21.4", "I10"], ["I21.4", "I10"]))
    assert r.fully_correct and r.principal_correct


def test_specificity_error_is_not_counted_as_wrong_condition():
    r = evaluate_case(case(["E11.65"], ["E11.9"]))
    assert r.specificity_errors == [("E11.65", "E11.9")]
    assert r.missed == [] and r.extra == []


def test_wrong_category_is_missed_plus_extra():
    r = evaluate_case(case(["B50.9"], ["B54"]))
    assert r.missed == ["B50.9"] and r.extra == ["B54"]


def test_sequencing_error():
    # Both codes correct, but pneumonia listed before sepsis
    r = evaluate_case(case(["A41.9", "J18.9"], ["J18.9", "A41.9"]))
    assert r.fully_correct and not r.principal_correct and r.sequencing_error


def test_no_ai_codes():
    r = evaluate_case(case(["J06.9"], []))
    assert r.missed == ["J06.9"] and not r.principal_correct


def test_invalid_format_is_flagged():
    r = evaluate_case(case(["I10"], ["I10", normalise_code("1234")]))
    assert r.invalid_format == ["123.4"]


# --- Aggregate metrics on the example data ------------------------------

def test_example_metrics():
    results = [evaluate_case(c) for c in load_cases(CASES)]
    s = summarise(results)
    assert (s.cases, s.reference_codes, s.ai_codes, s.exact_matches) == (20, 31, 30, 22)
    assert s.precision == 73.3 and s.recall == 71.0
    assert s.category_recall == 90.3


def test_specialties_sorted_weakest_first():
    results = [evaluate_case(c) for c in load_cases(CASES)]
    f1_scores = [s.f1 for s in by_specialty(results)]
    assert f1_scores == sorted(f1_scores)


# --- Loading data --------------------------------------------------------

def test_rejects_case_without_reference_codes(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("case_id,specialty,case_summary,reference_codes,ai_codes\nX1,Test,s,,I10\n")
    with pytest.raises(ValueError, match="no reference codes"):
        load_cases(bad)


def test_rejects_missing_columns(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("case_id,specialty\nX1,Test\n")
    with pytest.raises(ValueError, match="missing column"):
        load_cases(bad)


# --- Database and SQL queries -------------------------------------------

def test_database_and_every_sql_query_runs(tmp_path):
    db = tmp_path / "results.db"
    cases = load_cases(CASES)
    database.save(db, cases, [evaluate_case(c) for c in cases])
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 20
    queries = load_queries()
    assert len(queries) >= 5
    for name, sql in queries:
        con.execute(sql).fetchall()  # raises if any query is broken
    con.close()


# --- Command line ---------------------------------------------------------

def test_cli_json_output(capsys):
    assert main([str(CASES), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["overall"]["cases"] == 20
