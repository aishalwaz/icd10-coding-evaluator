"""Helpers for reading and checking ICD-10-CM codes.

An ICD-10-CM code has:
  * a 3-character CATEGORY (e.g. E11 = type 2 diabetes mellitus), then
  * an optional dot and up to 4 more characters that add SPECIFICITY
    (e.g. E11.65 = type 2 diabetes mellitus with hyperglycaemia).

Two codes in the same category describe the same condition at different
levels of detail. That lets us separate "wrong condition" errors from
"right condition, wrong specificity" errors.
"""

import re

# Letter, digit, letter-or-digit, then optionally a dot and 1 to 4 letters/digits.
_CODE_PATTERN = re.compile(r"^[A-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?$")


def normalise_code(raw: str) -> str:
    """Put a code into one standard form so that comparisons are fair.

    " e11.65 " -> "E11.65"   (trim spaces, upper-case)
    "E1165"    -> "E11.65"   (add the missing dot after the category)
    """
    code = raw.strip().upper().replace(" ", "")
    if len(code) > 3 and "." not in code:
        code = code[:3] + "." + code[3:]
    return code


def is_valid(code: str) -> bool:
    """True if a (normalised) code has a valid ICD-10-CM format.

    This checks the SHAPE of the code only, not whether it exists in the
    official code set.
    """
    return bool(_CODE_PATTERN.match(code))


def category(code: str) -> str:
    """Return the 3-character category, e.g. "E11.65" -> "E11"."""
    return code[:3]
