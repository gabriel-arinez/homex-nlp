# HOMEX real-voice audit — current semantic continuation and preserved history

## Current0.1.22 continuation

- [Executive report and verified limits](semantic-120-v1/evaluaciones/semantic-120-v1/final-report.md)
- [Current result/version index](semantic-120-v1/evaluaciones/semantic-120-v1/latest-evaluation.json)
- [All120 cases and14 comparison cells](semantic-120-v1/evaluaciones/semantic-120-v1/case-matrix.jsonl)
- [Complete four-cell comparisons for five candidate ASR settings](semantic-120-v1/evaluaciones/semantic-120-v1/comparison-v5/comparison.md)
- [ASR promotion decision and tradeoffs](semantic-120-v1/evaluaciones/semantic-120-v1/asr-selection.json)
- [Exact local reproduction commands](semantic-120-v1/evaluaciones/semantic-120-v1/reproduce/README.md)
- [Console logs](semantic-120-v1/logs/semantic-120-v1/)
- [Publication omission/redaction/hash ledger](semantic-120-v1/SEMANTIC-PUBLICATION-MANIFEST.json)

On unchanged original ASR, supported script-scalar coverage improved438/1000→487/1000,
with no previously matched scalar tuple lost; no-proposal cases23→17. This is NOT
full commercial precision or verified speech accuracy: acoustic/association
verification remains pending, and all120 recordings are development data.
Five complete candidate ASR settings (600decodes) and1680NLP case results are kept.
Context/VAD gain some fields but lose others, so production ASR remains unchanged.

Version0.1.22 has a new reproducible wheel, real installed-backend consumption,
891NLP/99relevant backend/306frontend passing tests, and8/8actual audio-to-form
checks across four forms. Source commit584e90b passed all four GitHub Actions jobs;
CI evidence always names its immutable commit, and delivery-commit status is
checked separately. No main merge, deployment or public package-registry release
is implied. Backend consumer7040564 is local pending explicit publication authority.
The later untracked backend scheduler database is preserved and not published.

The historical material below is frozen context, not the current version claim.

## Historical snapshot atb851b5a (preserved)

This branch publishes the implemented changes and the full evaluation results
requested by the user. It does **not** claim the original comprehensive audit is
finished. No PR, main merge, production deployment or package release is included.

## Start here

- [Progress report and limitations](evaluaciones/audit-120/progress-report.md)
- [Current snapshot index](evaluaciones/audit-120/latest-evaluation.json)
- [All120 before/after case results](evaluaciones/audit-120/120-case-results.jsonl)
- [Raw ASR transcriptions](evaluaciones/audit-120/transcriptions-baseline.jsonl)
- [Per-case matrix](evaluaciones/audit-120/case-matrix.csv)
- [Root causes and pending defects](evaluaciones/audit-120/root-cause-matrix.json)
- [Full console logs](logs/)
- [Independent publication check](evaluaciones/audit-120/publication-verification.json)
- [Source/export hashes and redactions](PUBLICATION-MANIFEST.json)

Current confirmed corpus:73 custom furniture,27chairs,7floating floors,13OTRO,
exactly120 IDs. All240 AAC/WAV hashes preserved; original recordings remain local.
Original Whisper Small CPU/int8 ASR baseline is unchanged. Script-relative WER
22.56%,CER18.14% is NOT verified spoken-reference/commercial accuracy. The partial
85-explicit-unit-price oracle improves62→65 matches on ASR input and67→70 on
reference input. Floor thickness3/7→6/7(ASR),3/7→7/7(reference). Full semantic
annotation, doubtful-audio adjudication and independent real-audio generalization
remain open; all120 examples are development data after being used for tuning.

Checks observed:799 NLP tests,99 backend tests,306 frontend tests; schemas/lint/
format/contracts/typecheck/build passed at the documented stages. Real browser/
Whisper/Django form application was verified for four forms and subsequently all
three poltronas on the latest source. Exact scopes, hashes, failures and successful
reruns are retained in the reports/logs, without claiming final commercial saving.

## Publication safety and history

All evaluaciones/ and logs/ artifacts plus current manifest, JSONL references and
control metadata are copied here. Raw local originals remain authoritative and
untouched. Only credentials/session tokens/password fill values in trace/config
COPIES were redacted; trace event counts, screenshots, timing, ASR text and fields
were preserved. Independent scanning found no uploaded audio payloads or surviving
credential values. Generated caches are excluded and accounted for in the ledger.
No original AAC/WAV corpus, model weights, host environment/keyring, database or
temporary dependency cache is included. Earlier baseline/chain snapshots are
intentionally retained as HISTORY; latest-evaluation.json identifies active views.

`packaging-smoke-only/` artifacts retain0.1.21 metadata for offline install/rebuild
checks and are **NOT releases**. Do not replace the previously published package
or backend vendor wheel with them. A separately versioned integration is pending.

## Reproduce

See [the repository runner guide](../../docs/real-voice-evaluation.md), the progress
report's exact commands, and each live-e2e reproduction folder. Supply the original
local corpus/model/dependencies separately. Output directories are exclusive;
keep new runs separate from immutable baseline and history. Public copies contain
redacted authentication material, so generate fresh synthetic test credentials.
