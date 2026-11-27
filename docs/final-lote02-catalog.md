# Catalog extraction keeps identity separate from quotations

The selected catalog category remains authoritative. Quoted counts and floor
areas no longer become part of chair, floor, or skirting names. Extraction is
stateless: it does not update inventory or invent commercial catalog records.

## Supported behavior

| Input shape | Result |
|---|---|
| `12 sillas ejecutivas con apoyo lumbar` | Name `sillas ejecutivas`; no stock or quantity mutation |
| `52 metros cuadrados de piso flotante laminado` | Name `piso flotante laminado`; area excluded from identity |
| Equivalent Spanish number words | Same boundaries, using the existing numeric grammar |
| `modelo NF Guión 7,782` | Complete identifier evidence unresolved for review; never `NF-7` |
| Explicit chair load, rotation, or reclining angle | Original technical phrase in `especificaciones`, with original-span evidence |
| Floor `espesor 80 mm` | Literal `80` retained and a field-level review requesting confirmation |
| Explicit skirting description or resistance/finish clause | Scoped `observaciones`, not an indiscriminate transcript copy |

## Conservative boundaries

- Model spelling remains all-or-unresolved. Missing letters are never supplied
  from a product lookup, reference script, or similarity guess.
- Punctuation between digits in a model is ambiguous: the extractor retains the
  whole span for confirmation instead of guessing whether it is a grouping or
  decimal separator.
- Floor thickness above 30 mm is a review heuristic, not a rejection limit or a
  replacement rule. Explicit atypical values remain unchanged.
- `OTRO` does not acquire chair/floor model or dimensional fields. Existing
  category conflicts, negations, active-value catalog matching, and raw offsets
  remain in place.
- New numeric technical phrases are preserved as descriptions, not silently
  converted into stock, furniture dimensions, or invented normalized values.

## Verification

Public-contract regressions live in `tests/unit/test_final_catalog.py`.
The initial run observed 13 failures and 3 passes before implementation; an
additional introduction and code-continuation cases observed RED before correction. The complete
focused and existing catalog suite then passed 207 tests. Existing tests were
not changed. A base/current public-API differential check preserved literal
chair models, ordinary floor thickness, `OTRO` model abstention, and category
isolation; the explicit skirting description gain was intentional.

No ASR, old evaluation audio, external model, persistence, or inventory operation
is involved.
