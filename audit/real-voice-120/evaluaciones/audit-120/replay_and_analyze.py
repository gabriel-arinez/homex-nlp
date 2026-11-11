"""Replay paired baseline text; partial manual financial/floor oracle, not full gold."""
import csv
import difflib
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from tools.evaluate_real_voice import extract, normalized_words

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'evaluaciones/audit-120'
BASE = OUT/(sys.argv[2] if len(sys.argv)>2 else 'baseline')
AFTER = OUT/(sys.argv[1] if len(sys.argv)>1 else 'after-nlp')
AFTER.mkdir(exist_ok=False)
(AFTER/'cases').mkdir()
values = json.loads((OUT/'catalog-fixture.json').read_text())
# Independent manual annotation from script number words; no production parser.
mp = [7300,4200,10000,5500,12000,2200,5200,5500,7300,15000,7300,3800,750,850,4000,1600,2900,2200,1200,1300,1200,1600,1600,3500,2200,2500,38900,29300,29800,25800,2000,9800,3800,2400,2550,3400,3400,1500,2800,6500,7200,3600,2800,1750,2000,950,3000,2800,3000,1600,1600,2500,1800,1600,1600,3000,2500,1950,7300,4200,10000,5500,12000,7300,4200,10000,5500,12000,1600,950,1200,3800,2500,4600,None,1500,1500,2800,2800]
sil = [5200,400,380,380,420,5200,1750,380,1200,1500,380,380,1700,1500,1500,1090,1080,550,1390,1400,1300,650,380,700,800,800,900,950,1990,560,980]
prices = {f'MP-{i:04}': v for i,v in enumerate(mp,1)}
prices.update({f'SIL-{i:04}':v for i,v in enumerate(sil,1)})
prices.update({f'PIS-{i:04}':v for i,v in enumerate([125,135,135,125,125,135,125],1)})
prices.update({f'OTR-{i:04}':v for i,v in enumerate([50,57,55],1)})
assert len(prices)==120

def amount(result, category):
    if category != 'MUEBLE_MEDIDA':return result.get('fields',{}).get('precio_lista')
    return ((result.get('item_proposal') or {}).get('price') or {}).get('stated_amount')

def semantic(result,category):
    if category != 'MUEBLE_MEDIDA':return result.get('fields',{})
    proposal=result.get('item_proposal')
    if not proposal:return None
    def clean(value):
        if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in {'evidence_ids','original_text'}}
        if isinstance(value,list):return [clean(v) for v in value]
        return value
    return clean(proposal)

rows=[]; annotations=[]; changes=[]
for p in sorted((BASE/'cases').glob('*.json')):
    r=json.loads(p.read_text());id=r['id'];category=r['category'];text=r['reference']
    expected=prices[id]
    if expected is None:mode='NOT_STATED'
    elif re.search(r'precio\s+(?:unitario|por juego|de lista)',text,re.I):mode='EXPLICIT_UNIT'
    else:mode='UNQUALIFIED_PRICE_REQUIRES_REVIEW'
    label={'id':id,'category':category,'stated_commercial_amount':str(expected) if expected is not None else None,
           'mode':mode,'currency':'BOB','basis':'Manual reading of original script number words; audio not independently reviewed',
           'other_fields_annotation':'PENDING','espesor_mm':'8' if category=='PISO_FLOTANTE' else None}
    annotations.append(label)
    after={'id':id,'category':category,'input_identity':r['audio'], 'reference_review':'PENDING_HUMAN_LISTENING'}
    changed=[]
    for input_type,key in [('reference','reference'),('asr','asr')]:
        input_text=text if input_type=='reference' else r['asr']['text_original']
        result,ms=extract(id+f'-{input_type}',category,input_text,values)
        after[f'nlp_{key}']=result;after[f'nlp_{key}_ms']=ms
        previous=r[f'nlp_{key}'];old=semantic(previous,category);new=semantic(result,category)
        if old!=new:
            changed.append(input_type)
            changes.append({'id':id,'input':input_type,'before':old,'after':new})
    old_amount=amount(r['nlp_asr'],category);new_amount=amount(after['nlp_asr'],category)
    ref_amount=amount(r['nlp_reference'],category);new_ref_amount=amount(after['nlp_reference'],category)
    def judge(actual):
        if expected is None:return 'CORRECT_ABSTENTION' if actual is None else 'UNEXPECTED_PRICE'
        if mode!='EXPLICIT_UNIT' and actual is None:return 'LEGITIMATE_MODALITY_REVIEW'
        if actual is None:return 'MISSING_OR_NO_PROPOSAL'
        return 'MATCH' if Decimal(actual)==expected else 'WRONG_AMOUNT'
    candidates=[]
    if r['metrics']['wer']['errors']:
        candidates.append('ASR_OR_REFERENCE_DISCREPANCY_PENDING_LISTENING')
    if judge(ref_amount) not in {'MATCH','CORRECT_ABSTENTION','LEGITIMATE_MODALITY_REVIEW'}:
        candidates.append('REFERENCE_INPUT_PRICE_FAILURE_OR_PROPOSAL_ABSTENTION')
    if judge(ref_amount)=='MATCH' and judge(old_amount)!='MATCH':
        candidates.append('ASR_OR_NORMALIZATION_PRICE_DISCREPANCY_PENDING_LISTENING')
    if changed:candidates.append('CONFIRMED_NLP_RULE_CORRECTION')
    if r['nlp_reference'].get('status')=='NO_PROPOSAL':
        candidates.append('NO_PROPOSAL_ROOT_CAUSE_REQUIRES_PRODUCT_REVIEW')
    expected_words=normalized_words(text);actual_words=normalized_words(r['asr']['text_original'])
    diff=[{'operation':op,'reference':expected_words[a:b],'asr':actual_words[c:d]}
          for op,a,b,c,d in difflib.SequenceMatcher(a=expected_words,b=actual_words,autojunk=False).get_opcodes() if op!='equal']
    after['word_diff']={'algorithm':'SequenceMatcher opcodes for inspection; metrics use Levenshtein','operations':diff}
    after['partial_oracle']=label
    after['error_candidates']=candidates
    after['manual_full_semantic_review']='PENDING'
    (AFTER/'cases'/p.name).write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
    row={'id':id,'category':category,'expected_amount':expected,'price_mode':mode,
         'before_reference_amount':ref_amount,'after_reference_amount':new_ref_amount,
         'before_asr_amount':old_amount,'after_asr_amount':new_amount,
         'before_reference_price_state':judge(ref_amount),'after_reference_price_state':judge(new_ref_amount),
         'before_asr_price_state':judge(old_amount),'after_asr_price_state':judge(new_amount),
         'wer':r['metrics']['wer']['rate'],'cer':r['metrics']['cer']['rate'],
         'changed_inputs':','.join(changed),'classification_candidates':';'.join(candidates),
         'review_state':'PENDING_LISTENING_AND_FULL_FIELD_ANNOTATION'}
    if category=='PISO_FLOTANTE':
        for prefix,record in [('before',r),('after',after)]:
            for key in ['asr','reference']:
                row[f'{prefix}_{key}_thickness']=record['nlp_'+key].get('fields',{}).get('espesor_mm')
    rows.append(row)
(AFTER/'partial-manual-oracle.json').write_text(json.dumps(annotations,ensure_ascii=False,indent=2)+'\n')
(AFTER/'semantic-changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
columns=list(dict.fromkeys(k for row in rows for k in row))
with (AFTER/'case-matrix.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)
summary={}
for category in sorted({r['category'] for r in rows}):
    group=[r for r in rows if r['category']==category]
    summary[category]={'cases':len(group),'partial_price_oracle':{},'changed_cases':[r['id'] for r in group if r['changed_inputs']]}
    for stage in ['before','after']:
        for key in ['asr','reference']:
            summary[category]['partial_price_oracle'][stage+'_'+key]=dict(Counter(r[stage+'_'+key+'_price_state'] for r in group))
    if category=='PISO_FLOTANTE':
        summary[category]['thickness_matches']={stage+'_'+key:sum(Decimal(r[stage+'_'+key+'_thickness'] or '0')==8 for r in group) for stage in ['before','after'] for key in ['asr','reference']}
(AFTER/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(AFTER/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('src').rglob('*.py'))},indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2));print('Semantic changes',len(changes)); print('Full semantic accuracy not computed; oracle covers commercial amount and floor thickness only.')
