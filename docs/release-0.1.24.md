# Commercial development candidate 0.1.24

This new candidate packages the confirmed focal review corrections without reusing the coherent 0.1.23 distribution identity. It preserves schema 1.0, RULES_ONLY mode, dependency pins and production Whisper Small CPU/int8. No model or ASR change is included.

## Corrected behavior

- Accessory context scans are bounded locally; explicit money is not an accessory count, and same-product compound corrections do not retain superseded quantities.
- Explicit dimension axes retain their own values and units, including adjective/axis distinctions.
- Composition, independent mentions and spoken catalog codes remain conservative; uncertain alternatives still require review.
- Catalog requests intentionally reject text longer than 20,000 characters. Exported request schemas carry the same bound.

See `sourcery-furniture-review.md` and `sourcery-catalog-review.md` for focused regression evidence and limitations. The 120 recordings remain DEVELOPMENT data; these changes do not establish acoustic accuracy, comprehensive commercial precision or independent generalization.

## Unpublished candidate replacement

The first unpublished 0.1.24 candidate was not promoted: frozen-development evaluation exposed two dimension false positives. This corrected second candidate adds the explicit-axis guard and its regressions. The original candidate artifacts, hashes and reports remain preserved privately; the current wheel identity is different. The 0.1.23 release identity is never reused.

## Distribution identity and verification

`catalog-release.json` records the new wheel identity. `catalog-release-0.1.23.json` preserves the previous current manifest byte-for-byte. All historical wheels, source archives and older manifests remain unchanged.

Two fresh builds use `SOURCE_DATE_EPOCH=0`; wheel and source archive bytes must match. Privacy checks reject audio (including AAC), model weights and secrets. The wheel contains only the runtime package; the source archive explicitly includes sanitized review documentation, benchmark tooling, tests and release history.

Installed verification uses an isolated copied environment, an ordinary no-dependency wheel installation and `python -I` outside the repository. All installed runtime modules must match both wheel and source bytes. Detailed check results and artifact hashes are recorded in the private `sourcery-review-v1/release-v2` evidence, not as embedded source-archive hashes.

Consumer integration and remote CI require separate final-HEAD evidence; packaging alone does not imply either passed. No publication, merge or deployment is performed by this release step.

Risk: item 5 (release identity and distribution contents).
