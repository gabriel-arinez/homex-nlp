"""Publish current audit views while preserving every earlier snapshot."""
import csv
import hashlib
import json
import shutil
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'evaluaciones/audit-120'
base=[json.loads(p.read_text()) for p in sorted((OUT/'baseline-routing-v2/cases').glob('*.json'))]
after={p.stem:json.loads(p.read_text()) for p in (OUT/'after-nlp-v4/cases').glob('*.json')}
assert len(base)==len(after)==120
assert Counter(r['category'] for r in base)==Counter(MUEBLE_MEDIDA=73,SILLA=27,PISO_FLOTANTE=7,OTRO=13)
backup=OUT/'before-poltronas/evaluaciones/audit-120'
for name in ['120-case-results.jsonl','transcriptions-baseline.jsonl','case-matrix.csv','partial-manual-oracle.json','diagnosis-initial.md','furniture-review-buckets.json']:
    dst=backup/name;assert not dst.exists();shutil.copy2(OUT/name,dst)
for name in ['case-matrix.csv','partial-manual-oracle.json']:
    shutil.copy2(OUT/'after-nlp-v4'/name,OUT/name)
with (OUT/'120-case-results.jsonl').open('w') as f:
    for r in base:f.write(json.dumps({'baseline':r,'after_nlp':after[r['id']]},ensure_ascii=False)+'\n')
with (OUT/'transcriptions-baseline.jsonl').open('w') as f:
    for r in base:f.write(json.dumps({'id':r['id'],'category':r['category'],'audio':r['audio'],'reference':r['reference'],'asr':r['asr'],'routing_provenance':r['routing_provenance']},ensure_ascii=False)+'\n')
latest={'classification':'user-confirmed10 commercial reclassifications;73 furniture,27 chairs,7 floors,13 other;120 total',
        'baseline':'baseline-routing-v2','after_nlp':'after-nlp-v4','frozen_original_execution':'baseline',
        'raw_asr_recomputed':False,'baseline_source_commit':'c94e7a89995a7157bd113a03bb8304321d30b0b1',
        'baseline_derivation':'derive_corrected_baseline.py; original source hashes/import verified; only three poltrona NLP results rerouted, no rule modifications',
        'correction_log':'reclassification.json','earlier_snapshots':'Historical only, preserved unmodified; not current category denominators',
        'full_semantic_accuracy':'NOT_ESTABLISHED','independent_generalization':'NOT_ESTABLISHED','publication':'PENDING'}
(OUT/'latest-evaluation.json').write_text(json.dumps(latest,indent=2)+'\n')
summary=json.loads((OUT/'baseline-routing-v2/summary.json').read_text())
metrics=['| Current category | Cases | WER | CER |','|---|---:|---:|---:|']
for cat,data in summary['categories'].items():
    metrics.append(f"|{cat}|{data['cases']}|{100*data['wer']['micro_rate']:.2f}%|{100*data['cer']['micro_rate']:.2f}%|")
metrics.append('|Overall|120|22.56%|18.14%|')
old=(OUT/'progress-report.md').read_text()
old_table=old[old.index('| Provisional category'):old.index('\n\nCase WER')]
report=old.replace(old_table,'\n'.join(metrics))
report=report.replace('Publication, definitive categories, full semantic annotation and\nindependent generalization evaluation remain OPEN.','Commercial category correction is complete for the10 confirmed records.\nPublication, full semantic annotation and independent generalization evaluation\nremain OPEN. Current snapshots are baseline-routing-v2 and after-nlp-v4;\nlatest-evaluation.json is the authoritative artifact index.')
report=report.replace('| Custom furniture |41|18→18|23→23|','| Custom furniture |38|18→18|23→23|')
report=report.replace('| Other |10|7→10|7→10|','| Other |13|10→13|10→13|')
report=report.replace('| Total |85|59→62|64→67|','| Total |85|62→65|67→70|')
report=report.replace('missing/no-proposal23 ASR cases and18 script cases remain.','missing/no-proposal20 ASR cases and15 script cases remain.')
report=report.replace('after-nlp-v3','after-nlp-v4')
report=report.replace('1. Business category of MP0004/0062/0067 (poltronas fijas) before definitive metrics.','1. RESOLVED: MP-0004/0062/0067 are OTRO, explicitly confirmed by the user.\n   Totals73 custom furniture/27 chairs/7 floors/13 other,120 cases. Original\n   raw baseline preserved; corrected baseline uses original rules at c94e7a8.\n   The three additional baseline price matches are a CORPUS ROUTING correction,\n   not an NLP improvement. Current before/after improvement is still three prices.')
report=report.replace('after-nlp-new\n','after-nlp-new baseline-routing-v2\n')
report=report.replace('- baseline/cases/*.json:120 raw ASR/paired NLP cases','- baseline/cases/*.json:120 historical original execution cases\n- baseline-routing-v2/cases/*.json:120 current-category baseline cases, immutable ASR\n- latest-evaluation.json: current snapshot pointers and provenance')
report=report.replace('before-reclassification/','before-reclassification/, before-poltronas/')
(OUT/'progress-report.md').write_text(report)
initial=(OUT/'diagnosis-initial.md').read_text()
(OUT/'diagnosis-initial.md').write_text('> Historical initial diagnosis. Category confirmation is now complete:73 furniture,27 chairs,7 floors,13 OTRO. Use latest-evaluation.json and progress-report.md for current metrics; initial execution is preserved below for traceability.\n\n'+initial)
buckets={}
for stage in ['baseline','after']:
    groups=defaultdict(list)
    for r in base:
        if r['category']!='MUEBLE_MEDIDA':continue
        n=r['nlp_reference'] if stage=='baseline' else after[r['id']]['nlp_reference']
        for w in n.get('warnings',[]):
            if w['code']!='RULES_ONLY_MODE':groups[w['code']].append(r['id'])
    buckets[stage]=dict(groups)
(OUT/'furniture-review-buckets.json').write_text(json.dumps(buckets,indent=2)+'\n')
matrix=json.loads((OUT/'root-cause-matrix.json').read_text())
for row in matrix:
    if row['id']=='C01':
        row['evidence']='reclassification.json:10 user-confirmed records; seven sillones and three poltronas MP-0004/0062/0067'
        row['root_cause_or_limitation']='Commercial corpus classification error, not an NLP rule defect. Original input text, IDs and audio paths unchanged; three old otros labels canonicalized. Corrected-category baseline retains original source and raw ASR.'
    if row['id']=='N06':row['evidence']=buckets['after'].get('MULTIPLE_MAIN_PRODUCTS',[])
    if row['id']=='N07':
        row['evidence']=buckets['after'].get('NO_PRODUCT',[])
        row['classification']='UNSUPPORTED_VOCABULARY'
        row['state']='PENDING_DOMAIN_TREATMENT'
        row['root_cause_or_limitation']='Remaining cubos móviles and estaciones require supported-domain treatment. Poltronas classification is resolved as OTRO and removed from this bucket.'
    if row['id']=='E01':row['root_cause_or_limitation']='Partial financial/floor oracle only. User-confirmed category routing complete; full-field annotation, hearing and independent real-audio evaluation remain open. All120 used for development.'
    for key,value in row.items():
        if isinstance(value,str):row[key]=value.replace('after-nlp-v3','after-nlp-v4')
(OUT/'root-cause-matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
with (OUT/'root-cause-matrix.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(matrix[0]));w.writeheader();w.writerows(matrix)
print(json.dumps({'categories':dict(Counter(r['category'] for r in base)),'latest':latest,
                  'three_poltrona_fields':{r['id']:{'reference':after[r['id']]['nlp_reference']['fields'],'asr':after[r['id']]['nlp_asr']['fields']} for r in base if r['id'] in {'MP-0004','MP-0062','MP-0067'}}},ensure_ascii=False,indent=2))
