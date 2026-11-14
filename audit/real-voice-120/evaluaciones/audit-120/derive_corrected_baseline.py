"""Reroute immutable ASR strings using original source and confirmed categories.

No inference, audio access, rule edits, or overwrite of the frozen baseline.
Run with original source on PYTHONPATH and --source-root pointing to its archive.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import homex_nlp
from tools.evaluate_real_voice import extract, summarize

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-root',type=Path,required=True)
args=parser.parse_args()
original_src=args.source_root.resolve()/'src'
assert Path(homex_nlp.__file__).resolve().is_relative_to(original_src)
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evaluaciones/audit-120'
base=OUT/'baseline'
target=OUT/'baseline-routing-v2'
target.mkdir(exist_ok=False);(target/'cases').mkdir()
refs_path=ROOT/'referencias/guiones_referencia_pregrabacion.jsonl'
refs={r['id']:r for r in map(json.loads,refs_path.read_text().splitlines())}
assert len(refs)==120
values=json.loads((OUT/'catalog-fixture.json').read_text())
identity=json.loads((base/'identity.json').read_text())
for rel,expected in identity['source_hashes'].items():
 assert hashlib.sha256((args.source_root/rel).read_bytes()).hexdigest()==expected
categories={'muebles_pedido':'MUEBLE_MEDIDA','sillas':'SILLA','pisos':'PISO_FLOTANTE','OTRO':'OTRO'}
changed=[]
for p in sorted((base/'cases').glob('*.json')):
 raw=p.read_bytes();row=json.loads(raw);ref=refs[row['id']]
 assert row['reference']==ref['guion']
 assert {k:v for k,v in row['source'].items() if k!='categoria'}=={k:v for k,v in ref.items() if k!='categoria'}
 previous_category=row['category'];new_category=categories[ref['categoria']]
 row['source']=ref;row['corpus_category']=ref['categoria'];row['category']=new_category
 row['routing_provenance']={'original_case':'baseline/cases/'+p.name,
                             'original_case_sha256':hashlib.sha256(raw).hexdigest(),
                             'original_category':previous_category,'effective_category':new_category,
                             'asr_recomputed':False,'initial_wall_time_semantics':'Original execution including previous NLP routing; new NLP timings recorded separately'}
 if previous_category!=new_category:
  assert row['id'] in {'MP-0004','MP-0062','MP-0067'}
  start=time.perf_counter()
  row['nlp_asr'],row['nlp_asr_ms']=extract(row['id'],new_category,row['asr']['text_original'],values)
  row['nlp_reference'],row['nlp_reference_ms']=extract(row['id']+'-ref',new_category,row['reference'],values)
  row['rerouting_elapsed_seconds']=time.perf_counter()-start
  assert 'fields' in row['nlp_asr'] and 'fields' in row['nlp_reference']
  assert row['nlp_asr']['category']==row['nlp_reference']['category']=='OTRO'
  changed.append(row['id'])
 assert row['asr']==json.loads(raw)['asr']
 with (target/'cases'/p.name).open('x') as f:json.dump(row,f,ensure_ascii=False,indent=2);f.write('\n')
assert set(changed)=={'MP-0004','MP-0062','MP-0067'}
new_identity=dict(identity)
new_identity['original_references_sha256']=identity['references_sha256']
new_identity['references_sha256']=hashlib.sha256(refs_path.read_bytes()).hexdigest()
new_identity['derivation']={'parent':'baseline','source_commit':'c94e7a89995a7157bd113a03bb8304321d30b0b1',
                            'source_import_verified':True,'rerouted_cases':changed,'asr_recomputed':False}
(target/'identity.json').write_text(json.dumps(new_identity,indent=2)+'\n')
env=json.loads((base/'environment.json').read_text());env['routing_derivation']=new_identity['derivation']
(target/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
summarize(target)
print('Original-source NLP rerouted:',changed,'; all120 raw ASR objects identical; no audio reopened.')
