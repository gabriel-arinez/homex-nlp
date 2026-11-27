# Preserve monetary amounts without inventing a mode

Currency-suffixed amounts and generic `precio` amounts now enter the existing
monetary mention parser. They reuse complete cardinal/mixed parsing, correction,
conflict, currency, negative-value, and truncation protection.

A valid ambiguous amount remains an unresolved `PRECIO_AMBIGUO` candidate.
`item_proposal.price` stays null: no unit/total mode or explicit origin is invented.
Only explicit root commercial quantity one supplies an arithmetic-equivalence
review suggestion. Missing quantities and internal accessory counts do not.

Regression: `tests/unit/test_residual_money.py`; existing monetary release,
mixed-amount, and final-money suites retain their explicit-mode checks.
