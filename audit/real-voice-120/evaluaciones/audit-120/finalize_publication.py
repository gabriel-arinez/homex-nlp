"""Finalize verified public copies; preserve raw originals and historical snapshots."""
import hashlib
import json
import shutil
from pathlib import Path

CORPUS=Path('/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz')
ROOT=Path('/home/gabriel/HOMEX/homex-nlp');OUT=CORPUS/'evaluaciones/audit-120';BUNDLE=ROOT/'audit/real-voice-120'
backup=OUT/'before-single-branch';backup.mkdir(exist_ok=False)
for name in ['latest-evaluation.json','progress-report.md']:shutil.copy2(OUT/name,backup/name)
latest=json.loads((OUT/'latest-evaluation.json').read_text())
latest.update(publication='SINGLE_BRANCH_EVIDENCE_SNAPSHOT',publication_branch='feat/real-voice-120-results',publication_repository='gabriel-arinez/homex-nlp',pull_request_strategy='NONE_USER_OVERRIDE',publication_manifest='../../PUBLICATION-MANIFEST.json',publication_proof='Remote branch ref is verified after push; transport receipt retained locally, outside this processing-results snapshot.')
(OUT/'latest-evaluation.json').write_text(json.dumps(latest,indent=2)+'\n')
p=OUT/'progress-report.md';s=p.read_text();s+='''
## Single-branch publication override

The user superseded the earlier chain plan and requested one published branch,
all implemented modifications and all evaluation results. Current destination:
`gabriel-arinez/homex-nlp`, branch `feat/real-voice-120-results`. No PR or merge.
The prior chain documents remain historical artifacts, not active instructions.
The full audit is still incomplete for the explicitly listed semantic/audio,
independent-evaluation and versioned-release limitations; publication does not
turn those pending criteria into completed results.

The public copy includes all evaluation/history/results/log snapshots and current
manifest/reference/control metadata. Independent privacy/fidelity verification
passed:120-case outputs/24 source hashes/category routing preserved;240 original
audio hashes retained; no original audio, session credentials, database/model or
cache published. Credential-bearing values in four Playwright traces/two configs
are redacted in COPIES; all trace events/screenshots remain. No source audio body
was present in those trace archives. Raw local evidence remains untouched.
See PUBLICATION-MANIFEST.json for source/export hashes and redaction details.
''';p.write_text(s)
# Safe new metadata below contains no credentials or raw trace material. Existing
# sanitized archives are NEVER replaced by their raw counterparts here.
manifest=json.loads((BUNDLE/'PUBLICATION-MANIFEST.json').read_text());records={r['source']:r for r in manifest['records']}
new=[OUT/'publication-verification.json',OUT/'finalize_publication.py',OUT/'latest-evaluation.json',OUT/'progress-report.md',*backup.iterdir(),CORPUS/'logs/audit-120-publication-verifier.log',CORPUS/'logs/audit-120-publication-export.log']
for source in new:
    rel=source.relative_to(CORPUS);target=BUNDLE/rel;target.parent.mkdir(parents=True,exist_ok=True);data=source.read_bytes();target.write_bytes(data)
    records[str(rel)]={'source':str(rel),'export':str(rel),'source_bytes':len(data),'export_bytes':len(data),'source_sha256':hashlib.sha256(data).hexdigest(),'export_sha256':hashlib.sha256(data).hexdigest(),'status':'IDENTICAL','note':'Final verification/publication metadata; no credential content.'}
manifest['records']=sorted(records.values(),key=lambda r:r['source'])
manifest['publication_branch']='feat/real-voice-120-results';manifest['pull_requests_or_merge']='NONE; user explicitly requested branch publication only'
manifest['snapshot_boundary']='All processing results/logs at final package preparation. Later Git transport output/remote receipt stay local to avoid a self-referential commit.'
manifest['independent_verification']='evaluaciones/audit-120/publication-verification.json (initial exported1287-record snapshot); final metadata additions additionally checked by parent.'
(BUNDLE/'PUBLICATION-MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(BUNDLE/'README.md').write_text('''# HOMEX real-voice audit — source changes and complete evidence snapshot

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
''')
print('Final publication metadata and README added; sanitized traces preserved.')
print('Manifest source entries:',len(manifest['records']))
