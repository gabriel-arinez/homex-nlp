# Residual subordinate component lists

A generic furniture root may introduce cabinets, sideboards, shelves, drawer
assemblies and modules as subordinate elements using the existing composition
connectors. Once such a list is established, `y` followed by a bare related
technical noun with a descriptive clause continues the list. A new commercial
article or quantity after the conjunction does not satisfy that rule.

Upper/lower qualifiers remain in each component identity, so independently
pronounced widths are associated with distinct components rather than the main
furniture. No axes, quantities or catalog records are synthesized. Generic module
mentions use the existing component contract.

Verification: `tests/unit/test_residual_compositions.py` observed five failures
and four passing independent-product guards before the change; after the change,
all nine pass, alongside the 29 existing furniture-relation checks. The complete
combined suite remains a separate seam check after the numeric/money units merge.

Risk: item 3 (shared product-reference and component parsing).
