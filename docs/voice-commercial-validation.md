# Abstain when speech has no commercial meaning

Catalog fallback names no longer turn greetings, testing phrases or numeric chatter into product proposals. A recognized product, descriptive commercial detail, or an explicit name declaration provides evidence; digits alone do not.

Valid brief descriptions such as `silla plegable` remain eligible. Unknown names can be declared explicitly, for example `nombre: Credenza Nórdica`, so extraction is not limited to a fixed product vocabulary. Insufficient text remains in the unrecognized evidence with a comprehensible warning rather than an invented product.

Custom furniture extraction also abstains on a bare `mueble` or `un mueble`. Dimensions, materials or actual component descriptions retain their existing valid interpretations. All evidence refers to original input spans.

The changes ship as local package 0.1.26 for the companion backend feature branch. No public release or publication is implied. Tests cover accepted descriptions, explicit new names, chatter, numeric noise, generic furniture and existing extraction regressions.
