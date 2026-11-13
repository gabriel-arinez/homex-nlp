# Preserve explicit commercial values without inventing a modality

This focused correction follows the product/component audit. It changes no public
schema, commercial classification, ASR model or production configuration.

## Demonstrated defects

- Commercial quantity recognized only the legacy one-to-ten word list, although
  a strict Spanish cardinal grammar already existed for dimensions/accessories.
  `Veinticinco escritorios` lost its quantity while `25 escritorios` worked.
  Prefix, explicitly labelled and postposed counts now reuse that strict grammar.
  Invalid alternatives, fractional suffixes and malformed cardinal expressions
  abstain; component/accessory quantities do not become commercial quantities.
- The explicit fused label `Preciunitario` was missed. It is accepted alongside
  the existing narrow label variants, retaining the original numeric evidence.
  `parece unitario` is not repaired: it can express real uncertainty. A generic
  `Precio de ...` still does not establish unit or negotiated-total modality.
- The truncated-number guard discarded punctuation while looking backward.
  Consequently, `un metro treinta por un metro treinta, ochenta centímetros de
  alto` lost its explicit height because the previous `treinta` appeared to be
  part of that number. Clause separators now bound this guard. The preceding
  geometry remains unresolved; the height retains its explicit unit, and a
  following unitless depth does not inherit centimetres.

`dos metros cinco`, `un metro 5` and malformed same-clause number chains remain
unresolved. No script value or alternative ASR output establishes what was heard.
Money without a verified modality remains a human-review item, not a fabricated
unit price. NLP totals are explanatory only; backend commercial authority remains.

## Verification

The public `RulesEngine.extract` regressions initially produced **17 failures and
16 passes**, after correcting an overly strict test expectation about the existing
numeric-only price evidence span. The earlier test attempt is retained separately.
After the changes, all **33** new probes pass, including existing digit/word count,
unit/total price behavior, negative alternatives and missing-unit boundaries.

```sh
.venv/bin/python -m pytest -q tests/unit/test_commercial_values_v3.py
.venv/bin/ruff check src/homex_nlp/rules.py tests/unit/test_commercial_values_v3.py
.venv/bin/ruff format --check src/homex_nlp/rules.py tests/unit/test_commercial_values_v3.py
```

All120 recordings remain development data. Re-evaluation reports scalar agreement
separately from acoustic, association and complete commercial precision.

Risk: item3 — shared integer/price/dimension rules; full regression, differential
checks, all120-case re-evaluation and independent verification are required.

The counted furniture-context guard reuses that same full cardinal grammar, not
the legacy one-to-ten list. Independent probes reproduced two additional misses
for word-only quantities/dimensions before this alignment; invalid cardinal
contexts remain rejected. The final focused file has37 parameterized probes.
