# NLP 0.1.25: literal retake dimensions and safe drawer references

Patch release from the verified retake corrections in commit3d28b1b. Schema1.0,
RULES_ONLY, ASR model and decoding settings remain unchanged. Catalog logic is
unchanged and retains its catalog-0.1.24 rules identity; the package is0.1.25.

- Articles such as `una altura de73cm` no longer produce false height1.
- Comma-separated desktop/drawer descriptions require positive dimensional
  evidence; independent orders and material-only ambiguities still abstain.
- Ordered x/× chains preserve literal values, declared/shared trailing units and
  explicit component ownership, without positional axis inference.
- Chain extraction does not expand existing explicit-dimension association.

See `directed-retakes-nlp.md` for boundaries. The15 directed recordings and120
historical cases remain development data, not acoustic certification. Table
sets, locker compartments, lateral credenzas and unknown axes still need review.

Version0.1.24 artifacts and manifest are preserved. New0.1.25 wheel identity is
recorded in `catalog-release.json`; isolated installed-consumer, reproducible
build, schema, full test and cross-repository CI checks must pass before merge.
Backend must update its strict version pin, vendored wheel/hash and lockfile;
no public contract or Frontend response shape change is introduced.
