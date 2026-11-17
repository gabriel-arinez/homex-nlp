# Voice integration CI correction

PR #47 initially failed `rules-only-freeze`: its current catalog release pointer still requested the 0.1.25 wheel from a fresh 0.1.29 build. The quality, package, secrets and dependency jobs otherwise passed.

`catalog-release.json` now describes the current reproducible CI build. The previous pointer is retained byte-for-byte as `catalog-release-0.1.25.json`, including in the source distribution. Existing historical manifests and backend wheel files are not replaced.

- NLP version: **0.1.29** (no runtime source change).
- CI `SOURCE_DATE_EPOCH=0` wheel: SHA-256 `a5590e607d2d10786c4b50b3effb119a1cb3de0ca3ecf12d7617724073a75aa0`.
- Existing backend wheel: SHA-256 `4e8ccb3362152e69ec552917a44c19f839b4f56c737a2e8997f3f23d4ebbff50`.
- Both archives have identical members; only ZIP timestamps differ (1980 CI epoch versus the original 2020 backend archive timestamp).
- RED: two manifest regression tests failed. GREEN: both passed; full source suite **1,211 passed**. Configured lint/format passed. The exact failed CI build/hash assertion passes locally.

This fixes the active release pointer without weakening its checksum gate or changing historical artifacts. GitHub CI and ordered main integration are tracked in the companion frontend `odd/tasks/voice-main-integration.md`.
