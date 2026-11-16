# Definitive commercial-validation correction

The existing rule engine is preserved. The correction is local to `feat/voice-hitl-review`; no package was published and no PR or merge was created.

## Behavior

- Explicit `producto:`, `nombre:` and `nombre comercial:` prefixes do not bypass commercial-content validation.
- Greetings, counting, microphone-test phrases and attribute markers without values abstain; legitimate introduced names remain open vocabulary.
- Category contradictions use the primary product identity, not a related noun: chair descriptions remain valid when mentioning desks, and flooring remains valid when mentioning a room with chairs.
- Typed `field_reviews` link actual extracted fields and candidate IDs to commercial warnings, including an accepted price requiring human review. Existing warning strings remain compatible.
- Furniture prefix negatives, quantities, dimensions, materials, prices and rectifications retain their regressions.

## Verified final candidate

| Check | Result |
| --- | --- |
| Full source suite | 1,185 passed |
| Full suite against the installed wheel | 1,185 passed |
| Independent commercial regression subset | 197 passed |
| Ruff and formatting | Passed |
| Extraction schema drift | Passed |
| Canonical wheel and sdist reproducibility | Passed, `SOURCE_DATE_EPOCH=0` |

Specific RED evidence: 22 explicit-name/category failures, two primary-versus-related-noun failures, and three bare microphone-test-phrase failures before their fixes. Existing furniture-prefix negatives already abstained. Positive category fixtures were moved to their intended category rather than weakening the new contradiction rule.

## Artifact identity

New local version: **0.1.28**. The backend vendors and installs `homex_nlp-0.1.28-py3-none-any.whl`.

SHA256: `abf68e16979c9cdf64eff534051798cec3a12b9d27672fd0f9fcd4805e825fea`.

Installed module bytes, metadata, runtime guard, backend lock and operational checksum pins agree. Historical 0.1.25, 0.1.26 and 0.1.27 artifacts remain unchanged. The cross-component report is maintained in the frontend repository at the same documentation path.

Risk: items 3 and 5 — additive consumed review contract and coordinated local package integration. Full producer/consumer tests and independent checks cover these changes. Browser speech tests use synthetic fixtures, not a claim of field speech accuracy.
