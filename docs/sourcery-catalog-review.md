# Keep model spelling distinct from ordinary prose

Supported chair and floating-floor extraction now accepts complete codes containing
the spoken letter O without treating ordinary model descriptions as ambiguous codes.
The `OTRO` category remains unchanged and does not extract model fields.

## Review examples

| Input | Model outcome |
|---|---|
| `Modelo B O dos` / `Código B O 2` / `Modelo be o dos` | `BO2`, with the original spelling span |
| `Modelo B o modelo C` / `Modelo B, o mejor C` | Unresolved; no invented or silently selected model |
| `modelo a medida` / `modelo de madera` / `modelo de` | Ordinary prose, not model-code evidence or ambiguity warnings |
| `modelo be zeta` / `modelo be zeta guion` | Incomplete spelling remains unresolved |
| `modelo de 43` / `modelo a nueve` | Uncertain initial spelling remains unresolved |
| `modelo A1` / `modelo D2` / `modelo XT-072` | Existing literal codes remain intact |
| `modelo B quince` | Existing mixed-shorthand abstention remains intact |

## Grammar boundary

The existing decoder still requires a complete alphanumeric code with both a letter
and a number. A written initial can begin spelling when another spelled letter
follows; it does not make previously uncertain mixed shorthand authoritative.
An O after a numeric component remains unresolved because it can join alternatives,
as in `modelo be zeta uno o dos`. This intentionally conservative rule does not
claim to recognize every possible commercial code.

A small internal status helper distinguishes `NOT_CODE`, `AMBIGUOUS`, and `CODE`.
Only ordinary leading `a`/`de` phrases bypass model evidence; literal codes such as
`A1` and `D2` are not filtered by their first letter. Accepted and unresolved
candidates retain offsets into the untouched source text. No category, public
schema, version, dependency, or consumer metadata changes are part of this unit.

## Verification

Public `extract_catalog` regressions cover both supported categories, original
source evidence, unresolved alternatives, existing literal/spoken codes, and the
unsupported `OTRO` boundary. The focused regression command is:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_sourcery_catalog_review.py tests/unit/test_catalog.py tests/unit/test_catalog_semantic_v2.py
```

Baseline differential checks compare serialized public results, stderr, and exit
status using separate source trees. They are source-level compatibility evidence,
not proof of an installed distribution or consumer integration.
