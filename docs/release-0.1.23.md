# Commercial development candidate 0.1.23

This candidate adds conservative product/component relations and explicit commercial values, alongside a local-only human review utility for the 120 original recordings. It preserves schema 1.0, RULES_ONLY operation and the production Whisper Small CPU/int8 configuration. No NER/research model or runtime browser dependency is introduced.

## Scope and limits

- Relations distinguish integrated furniture/components, explicit product evidence and legitimate abstention; no case-ID conditions are used.
- Explicit integrated `credencia` and `credenza` share component-family recognition while preserving the literal name and offsets. Their dimensions/material remain component-local rather than becoming desktop fields; independent orders and unqualified/non-furniture mentions retain conservative abstention.
- Values cover prefix word quantities, fused explicit unit prices and independently stated height without manufacturing missing units or resolving ambiguous money.
- The offline review utility exposes script, ASR, commercial fields and original audio for human adjudication. Node/browser probes are optional development checks, not runtime dependencies.
- The distribution guard now rejects `.aac` case-insensitively outside audio directories as well. This closes a latent guard gap; it does not establish that previous artifacts leaked audio.

All 120 recordings are DEVELOPMENT data. Human acoustic and association verification remain at zero. Preliminary scalar coverage of 548/1000 after the relations-only stage is not final precision, acoustic accuracy, comprehensive commercial accuracy or evidence of generalization. Final evaluation remains separate and version-bound.

## Distribution identity

See `catalog-release.json` for the exact wheel SHA-256. `catalog-release-0.1.22.json` preserves the previous current manifest byte-for-byte; historical 0.1.20/0.1.21 manifests and all previous local distributions remain unchanged. Only the `homex_nlp` runtime package enters the wheel; sanitized tools, static review assets and release documentation enter the sdist explicitly. Private audio, full audit corpora, `.atl`, models and environment secrets are excluded.

Reproducibility uses two fresh wheel/sdist outputs with `SOURCE_DATE_EPOCH=0`. Installed proof uses an isolated copied environment, an ordinary no-dependency wheel installation and `python -I` outside the repository. Every installed Python module must match both wheel and source bytes; no NLP `PYTHONPATH` override is allowed. Detailed logs and final check counts live in the local commercial review release-v2 evidence, not in this document's claims.

The earlier 0.1.23 release-v1 wheel was an unpublished intermediate candidate, not a published release; its artifacts and identities remain preserved privately.

Consumer integration and remote CI evidence must match this release separately; building the wheel does not imply either passed. No publishing, main merge or deployment is performed here.

Risk: item 2 (privacy guard) and item 5 (release metadata and CI step description).
