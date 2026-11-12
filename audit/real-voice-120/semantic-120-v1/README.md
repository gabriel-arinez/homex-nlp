# Semantic120 evidence publication

Start with `evaluaciones/semantic-120-v1/final-report.md` and `latest-evaluation.json`.
The exact commands are in `reproduce/README.md` under that evaluation directory.

This snapshot includes all120 case records, all600 controlled ASR results, the14-cell1680-result NLP comparison, field references/provenance, source and consumer identities, regressions, failed attempts and console logs. All120 are development data; acoustic/association adjudication and independent-audio evaluation remain pending. Supported script-scalar coverage is not full commercial precision.

No recording, replay clip, model weight, database, credential or intermediate wheel binary is published. The source/export/hash omission ledger is `SEMANTIC-PUBLICATION-MANIFEST.json`. Raw traces remain private: only sanitized text event streams and final screenshots are distributed, not thousands of redundant screencast frames. Private historical runtime helpers are omitted; references to them in copied historical READMEs describe the local source archive, not files in this public snapshot. Use only the fresh-credential portable `*-v3` bootstrap/helpers for reproduction. That portable wrapper was structurally checked, not rerun after portability changes; the observed original integration-v3 passed8/8 actual audio-to-form scenarios.

The original b851b5a audit under the parent directory is preserved as historical evidence. Current references are references-v2 and current semantic comparison is comparison-v5; superseded intermediate runs are labeled in latest-evaluation.json. Backend7040564 is local pending explicit remote publication authorization. No main merge or production deployment is implied.
