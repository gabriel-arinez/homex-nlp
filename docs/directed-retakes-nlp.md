# Literal measurements and conservative desktop references

The RULES_ONLY extractor retains ordered `x`/`×` dimension chains without assigning
width, depth or height from their position. The public schema remains 1.0; an
unknown axis is represented by the existing nullable `axis` field. Every result
still requires review, not commercial approval.

## Supported evidence

- `una altura de 73 cm` contains one height, 73 cm; the article is not height1.
- Bare comma restatements of an already introduced desktop or its drawer are
  descriptive references, just like sentence-separated restatements. Explicit
  new quantities, independent conjunctions, alternatives and unrelated products
  still abstain. Bare comma merging requires positive dimensional evidence and
  is restricted to the desktop relation path; `cajonera de madera` stays ambiguous.
- `1,40 m × 70 cm` retains both declared units, literal order and exact spans.
- `33 × 40 × 63 cm` has one trailing unit scoped to the homogeneous list. All
  three values retain the full chain as unit evidence. A mixed-unit chain such
  as `1 m × 40 × 63 cm` leaves the middle unit unknown, not guessed.
- Existing oral metre-plus-centimetre forms are recognized in chains as well.
- A chain is assigned only to its directly described product/component. A new
  clause, unknown owner, non-positive value, negation or overlapping explicit
  axis evidence prevents automatic chain interpretation. Full chain evidence
  stays unresolved when interpretation is unsafe. Axes always remain unknown.

Dimension-chain preservation runs after the existing explicit-dimension
association pass. This prevents newly extracted chains from silently extending
that pass and moving an existing desktop height onto a drawer. Literal operand
candidates and unresolved whole-chain evidence remain available for review.

## Boundaries and verification

No script, corpus ID, expected quantity, price or acoustic model is consulted by
these rules. New takes can therefore produce different quantities: each is
preserved, and unit-price totals use only the recognized input quantity. Missing
units or price modality still need confirmation. Sets of different tables,
lockers versus compartments and non-integrated lateral credenzas remain unresolved.

Public API regression tests are in `tests/unit/test_directed_retakes.py`. Private
15-take and 120-case before/after evidence lives outside the repository. Checks
compare values, units, component ownership, amounts and abstentions, not only
proposal status. These development comparisons do not establish human acoustic
precision or independent generalization. Existing installed-consumer contract
and schema checks remain applicable; no consumer repository changes are needed.

## Release review hardening

Comma references validate every chain operand as positive before merging; malformed
or zero chains do not establish a reference. Existing metre aliases `mt`/`mts`
are retained. A chain overlapping an already interpreted thickness remains
unresolved instead of asserting the same evidence as both thickness and dimension.
The measurement/owner index is built once per extraction; it does not repeatedly
scan growing dimension/candidate cross-products for every chain. Quantity-bearing
independent orders, including eleven drawers, continue to abstain.
