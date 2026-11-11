"""Advance current report pointers after verified numeric-name correction."""
import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'evaluaciones/audit-120'
backup=OUT/'before-numeric-name';backup.mkdir(exist_ok=False)
for name in ['latest-evaluation.json','120-case-results.jsonl','transcriptions-baseline.jsonl','case-matrix.csv','partial-manual-oracle.json','progress-report.md','root-cause-matrix.json','root-cause-matrix.csv']:
    shutil.copy2(OUT/name,backup/name)
latest=json.loads((OUT/'latest-evaluation.json').read_text());latest['after_nlp']='after-nlp-v5'
latest['candidate_source_snapshot']='candidate-source-v2'
latest['latest_integration']='live-e2e-poltronas;3 actual OTRO uploads against current24 source hashes, plus previous4-form evidence retained separately'
(OUT/'latest-evaluation.json').write_text(json.dumps(latest,indent=2)+'\n')
base=[json.loads(p.read_text()) for p in sorted((OUT/'baseline-routing-v2/cases').glob('*.json'))]
after={p.stem:json.loads(p.read_text()) for p in (OUT/'after-nlp-v5/cases').glob('*.json')}
assert len(base)==len(after)==120
for name in ['case-matrix.csv','partial-manual-oracle.json']:shutil.copy2(OUT/'after-nlp-v5'/name,OUT/name)
with (OUT/'120-case-results.jsonl').open('w') as f:
    for row in base:f.write(json.dumps({'baseline':row,'after_nlp':after[row['id']]},ensure_ascii=False)+'\n')
report=(OUT/'progress-report.md').read_text()
report=report.replace('five bounded','six bounded').replace('after-nlp-v4','after-nlp-v5').replace('suite790passed','suite799passed')
report=report.replace('24 semantic output changes across13 IDs','26 semantic output changes across15 IDs')
report=report.replace('- Independent scratch probes preserve legacy CLI output', '- Latest numeric-name batch: RED3failed/27passed; GREEN74 focused/catalog tests;\n  final suite799passed. Two additional ASR cases (MP0004/0062) now retain literal\n  numeric-leading names and full observations without inventory/quantity inference.\n- Latest source backend99passed; three ACTUAL poltrona audio→Chromium→Whisper→\n  Django/PostgreSQL→OTRO application checks passed for MP0004/0062/0067 at5500.\n  Observations equal raw ASR input; zero commercial writes or inventory changes.\n  All24 current source hashes match after-nlp-v5 and all240 audio hashes are intact.\n  This is additional latest-candidate proof, not a replacement of older4-form traces.\n- Independent scratch probes preserve legacy CLI output')
report=report.replace('- live-e2e-final/: browser responses/screenshots/traces, hashes/reproduction', '- live-e2e-final/: previous four-form browser evidence;\n- live-e2e-poltronas/: latest-candidate real poltrona responses/screenshots/traces, hashes/reproduction\n- candidate-source-v2/: exact latest local candidate; latest-evaluation.json indexes active snapshots')
report=report.replace('Unsupported vocabulary','Unsupported vocabulary')
(OUT/'progress-report.md').write_text(report)
matrix=json.loads((OUT/'root-cause-matrix.json').read_text())
for row in matrix:
    for key,value in row.items():
        if isinstance(value,str):row[key]=value.replace('after-nlp-v4','after-nlp-v5')
matrix.append({'id':'N11','classification':'NLP_NAME_BOUNDARY','commercial_impact':'Natural ASR catalog name/description omitted',
               'evidence':'MP-0004/0062 ASR inputs start 2 poltronas; tests use3 paneles across all3 catalog categories; live-e2e-poltronas',
               'state':'CORRECTED_CONFIRMED',
               'root_cause_or_limitation':'Initial noun phrase required alphabetic first character, so digit-rendered count prevented literal name and full observations. Allow positive integer prefix with no inferred quantity/stock; unit/amount-only,zero/negative/negation/admin starts remain abstained. Full description reaches OTRO UI unchanged.'})
(OUT/'root-cause-matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
with (OUT/'root-cause-matrix.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(matrix[0]));w.writeheader();w.writerows(matrix)
snapshot=OUT/'candidate-source-v2';snapshot.mkdir(exist_ok=False)
for path in [*Path('src').rglob('*.py'),Path('tools/evaluate_real_voice.py'),Path('tests/unit/test_real_voice_regressions.py'),Path('tests/evaluation/test_real_voice.py'),Path('docs/catalog-voice.md')]:
    dest=snapshot/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
for row in json.loads((OUT/'audio-ledger.json').read_text()):
    for entry in row['audio'].values():assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']
print('Current reports advanced to baseline-routing-v2/after-nlp-v5;120 cases,26 changed outputs over15 IDs,240 original audio hashes unchanged.')
print('Classification complete73/27/7/13; full semantic evaluation/publication still OPEN.')
