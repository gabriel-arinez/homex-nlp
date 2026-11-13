# Real-voice semantic candidate0.1.22

This separately versioned package preserves the public schema and ASR production configuration. It improves conservative furniture references, material/accessory association evidence, bounded catalog names, explicit HDF gauges and strict spoken model codes. Ambiguous prepositions and alternative counts abstain. No stock, permissions, approved price or product state is authoritative in NLP.

Wheel: `homex_nlp-0.1.22-py3-none-any.whl`  
SHA-256: `c1a085f899a9f2f0797f332304fcf8eeea91f4837d5d06a9a2ca5a6c07815a80`

`docs/catalog-release-0.1.21.json` preserves the historical manifest byte-for-byte; local historical distributions and existing backend vendor wheel are not removed. Intermediate unpublished local candidates are not releases. The final installed backend consumer must match the new SHA and import from its own site-packages, not local NLP sources.

## Reproduce

```bash
uv sync --locked --extra dev --extra asr
make check
SOURCE_DATE_EPOCH=0 uv build
UV_OFFLINE=1 .venv/bin/python tools/verify_distribution.py
```

At final source freeze,891 tests, lint/format, schemas and corpus checks passed. Two offline deterministic builds produced identical wheel/sdist bytes; the wheel hash matches the manifest and backend vendor. Independent verification checked the explicit-name provenance correction and installed-wheel context guards. Consumer integration and remote CI evidence are version-bound separately, not implied by a successful build.

The120 recordings remain development data. Script-scalar coverage is not acoustic accuracy, full semantic precision or demonstrated generalization. Human acoustic/association adjudication remains pending; replay clips stay local. See the audit continuation reports and console logs for exact results, failures and limitations.

Risk: items3(shared semantic evidence consumers) and5(distribution and consumer version binding).
