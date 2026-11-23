"""Compare AI codes with reference codes and calculate accuracy metrics.

Key terms (for one set of cases):
  * Exact match     : the AI code is identical to a reference code.
  * Specificity error: the AI code is in the same 3-character category as a
                      missed reference code (right condition, wrong detail).
  * Missed code     : a reference code the AI did not give.
  * Extra code      : an AI code that is not in the reference set.
  * Precision       : of the codes the AI gave, the share that were correct.
                      (exact matches / all AI codes)
  * Recall          : of the codes it should have given, the share it found.
                      (exact matches / all reference codes)
  * F1 score        : one number that balances precision and recall.
  * Principal diagnosis accuracy: the share of cases where the AI's FIRST
                      code matches the reference's first code (sequencing).
"""

from collections import defaultdict
from dataclasses import dataclass, field

from .codes import category, is_valid


@dataclass
class CaseResult:
    case_id: str
    specialty: str
    n_reference: int
    n_ai: int
    exact: list = field(default_factory=list)
    specificity_errors: list = field(default_factory=list)  # (reference, ai) pairs
    missed: list = field(default_factory=list)              # wrong condition or not coded
    extra: list = field(default_factory=list)               # AI codes with no matching category
    invalid_format: list = field(default_factory=list)
    principal_correct: bool = False
    principal_reference: str = ""
    principal_ai: str = ""
    sequencing_error: bool = False  # right codes found, but the wrong one listed first

    @property
    def fully_correct(self) -> bool:
        """True when the AI's code set is exactly the reference code set."""
        return len(self.exact) == self.n_reference == self.n_ai


def evaluate_case(case) -> CaseResult:
    """Score a single case."""
    reference, ai = case.reference_codes, case.ai_codes

    exact = [c for c in reference if c in ai]
    missed_ref = [c for c in reference if c not in ai]
    extra_ai = [c for c in ai if c not in reference]

    # Pair each missed reference code with an extra AI code from the same
    # category: these are specificity errors, not wrong diagnoses.
    specificity, unpaired_extra = [], list(extra_ai)
    still_missed = []
    for ref_code in missed_ref:
        partner = next((a for a in unpaired_extra if category(a) == category(ref_code)), None)
        if partner:
            specificity.append((ref_code, partner))
            unpaired_extra.remove(partner)
        else:
            still_missed.append(ref_code)

    return CaseResult(
        case_id=case.case_id,
        specialty=case.specialty,
        n_reference=len(reference),
        n_ai=len(ai),
        exact=exact,
        specificity_errors=specificity,
        missed=still_missed,
        extra=unpaired_extra,
        invalid_format=[c for c in ai if not is_valid(c)],
        principal_correct=bool(ai) and ai[0] == reference[0],
        principal_reference=reference[0],
        principal_ai=ai[0] if ai else "",
        # Sequencing error: the AI's first code is correct for the case but is not
        # the principal diagnosis, e.g. pneumonia listed before sepsis.
        sequencing_error=bool(ai) and ai[0] != reference[0] and ai[0] in reference,
    )


def _ratio(part, whole) -> float:
    """Percentage rounded to 1 decimal place; 0 when there is nothing to divide by."""
    return round(100 * part / whole, 1) if whole else 0.0


@dataclass
class Summary:
    label: str
    cases: int
    reference_codes: int
    ai_codes: int
    exact_matches: int
    specificity_errors: int
    missed: int
    extra: int
    precision: float
    recall: float
    f1: float
    category_recall: float   # counts right-category codes as found
    case_accuracy: float     # cases where the whole code set is correct
    principal_accuracy: float


def summarise(results, label="All cases") -> Summary:
    """Combine many CaseResults into one set of metrics (micro-averaged)."""
    n_ref = sum(r.n_reference for r in results)
    n_ai = sum(r.n_ai for r in results)
    n_exact = sum(len(r.exact) for r in results)
    n_spec = sum(len(r.specificity_errors) for r in results)

    precision = _ratio(n_exact, n_ai)
    recall = _ratio(n_exact, n_ref)
    f1 = round(2 * precision * recall / (precision + recall), 1) if precision + recall else 0.0

    return Summary(
        label=label,
        cases=len(results),
        reference_codes=n_ref,
        ai_codes=n_ai,
        exact_matches=n_exact,
        specificity_errors=n_spec,
        missed=sum(len(r.missed) for r in results),
        extra=sum(len(r.extra) for r in results),
        precision=precision,
        recall=recall,
        f1=f1,
        category_recall=_ratio(n_exact + n_spec, n_ref),
        case_accuracy=_ratio(sum(r.fully_correct for r in results), len(results)),
        principal_accuracy=_ratio(sum(r.principal_correct for r in results), len(results)),
    )


def by_specialty(results) -> list:
    """One Summary per specialty, weakest (lowest F1) first."""
    groups = defaultdict(list)
    for r in results:
        groups[r.specialty].append(r)
    summaries = [summarise(group, label=name) for name, group in groups.items()]
    return sorted(summaries, key=lambda s: (s.f1, s.label))
