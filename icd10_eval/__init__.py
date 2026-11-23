"""ICD-10-CM Coding Accuracy Evaluator.

Compares an AI model's ICD-10-CM codes with expert reference codes and
reports how accurate the model is, overall and by specialty.
"""

from .codes import category, is_valid, normalise_code
from .data import Case, load_cases
from .metrics import CaseResult, Summary, evaluate_case, summarise

__version__ = "0.1.0"

__all__ = [
    "Case", "CaseResult", "Summary",
    "category", "is_valid", "normalise_code",
    "evaluate_case", "load_cases", "summarise",
]
