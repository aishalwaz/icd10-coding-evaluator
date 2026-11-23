# ICD-10-CM Coding Accuracy Evaluator

A Python tool that measures how accurately an AI model assigns ICD-10-CM diagnosis codes. It compares the model's codes with expert reference codes across a set of clinical cases and shows not just *how often* the model is wrong, but *how* it is wrong.

I built this to reflect how I evaluate AI clinical coding: a dataset of synthetic cases with reference codes, AI-generated codes benchmarked against them, and error analysis by specialty.

## What it measures

| Metric | Meaning |
|---|---|
| **Precision** | Of the codes the AI gave, the share that were correct |
| **Recall** | Of the codes it should have given, the share it found |
| **F1 score** | One number balancing precision and recall |
| **Category recall** | Recall when the right 3-character category counts (right condition, wrong detail) |
| **Principal diagnosis accuracy** | Share of cases where the AI's first-listed code is the correct principal diagnosis |
| **Fully correct cases** | Share of cases where the AI's code set matches the reference exactly |

Every error is classified:

- **Specificity**: right condition, wrong detail, e.g. `E11.9` given for `E11.65` (hyperglycaemia not captured), or `S72.002A` (left) for `S72.001A` (right)
- **Missed**: a reference code the AI did not give, e.g. a secondary diagnosis or a `Z3A` weeks-of-gestation code
- **Extra**: a code that should not be there, e.g. coding fever (`R50.9`) when it is integral to the diagnosed infection
- **Sequencing**: correct codes, but the wrong one listed as the principal diagnosis, e.g. pneumonia before sepsis
- **Format**: a code that is not a valid ICD-10-CM shape

## Example

```bash
python -m icd10_eval.cli examples/cases.csv
```

```
Precision:            73.3%
Recall:               71.0%
F1 score:             72.1%
Category recall:      90.3%
Principal diagnosis:  65.0%

ERROR LOG (12)
C001  specificity  expected E11.65, AI gave E11.9
C003  missed       B50.9
C003  extra        B54
C006  sequencing   J18.9 listed first; principal diagnosis is A41.9
...
```

The gap between recall (71%) and category recall (90%) shows that most of this model's errors are specificity errors rather than wrong diagnoses.

Output is also available as Markdown or JSON:

```bash
python -m icd10_eval.cli examples/cases.csv --format markdown
python -m icd10_eval.cli examples/cases.csv --format json
```

## SQL analysis

Save everything to a SQLite database, then run the ready-made queries in `queries/analysis.sql`:

```bash
python -m icd10_eval.cli examples/cases.csv --db results.db
python -m icd10_eval.query results.db
```

Included queries: accuracy by specialty, most frequently missed codes, specificity errors, error types overall, and cases with the wrong principal diagnosis. The database can also be opened in any SQLite tool, such as DB Browser for SQLite.

Tables: `cases`, `codes` (every reference and AI code, with position and category), `results` (scores per case) and `errors` (one row per coding error).

## Using your own data

Create a CSV with these columns. Separate multiple codes with `;` and list the principal diagnosis first. Dots are optional (`E1165` is read as `E11.65`).

```csv
case_id,specialty,case_summary,reference_codes,ai_codes
C001,Internal Medicine,58-year-old with type 2 diabetes and hyperglycaemia; hypertension.,E11.65;I10,E11.9;I10
```

## Project structure

```
icd10_eval/
  codes.py     normalise and validate codes
  data.py      load cases from CSV
  metrics.py   compare codes, classify errors, calculate metrics
  database.py  save to SQLite
  query.py     run the SQL analysis queries
  report.py    text, Markdown and JSON output
  cli.py       command-line interface
examples/      20 synthetic cases across 12 specialties
queries/       SQL analysis queries
tests/         automated tests (pytest)
```

## Run the tests

```bash
pip install pytest
python -m pytest
```

No other dependencies; the tool uses only the Python standard library.

## Limitations and next steps

- Format validation checks a code's shape, not whether it exists in the current official code set.
- Category matching treats any code in the same 3-character category as the same condition, which is a simplification.

Planned: validation against the official CMS ICD-10-CM code list, partial credit weighting, and charts of accuracy by specialty.

## Disclaimer

All cases are synthetic. For AI evaluation and research only, not for billing or clinical use. Check codes against the current ICD-10-CM release and official coding guidelines.

## Author

**Aisha Aliyu Waziri, MBBS** · Medical Doctor and Healthcare AI Evaluation Specialist

Also see: [Clinical LLM Response Grader](https://github.com/aishalwaz/clinical-llm-grader)
