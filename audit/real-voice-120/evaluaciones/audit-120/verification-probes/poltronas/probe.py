import json,os,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]); repo=Path('/home/gabriel/HOMEX/homex-nlp'); py=repo/'.venv/bin/python'; common=os.environ.copy()
def run_py(tree,code):
 env=common.copy();env['PYTHONPATH']=str(root/tree/'src');env['TMPDIR']=str(root/'tmp')
 return subprocess.run([str(py),'-c',code],cwd=root/tree,env=env,text=True,capture_output=True)
cat_code=r'''import json
from homex_nlp.catalog import CatalogRequest,extract_catalog
text=__import__('sys').argv[1]
r=extract_catalog(CatalogRequest(category='OTRO',text=text))
print(json.dumps(r.model_dump(mode='json'),ensure_ascii=False,sort_keys=True))'''
# Actual original ASR inputs, derived from frozen baseline (not hand-edited).
base_cases=Path('/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz/evaluaciones/audit-120/baseline-routing-v2/cases')
for id in ('MP-0004','MP-0062','MP-0067'):
 case=json.load(open(base_cases/(id+'.json'))); text=case['asr']['text_original']
 print('ACTUAL_ASR',id,'text=',text)
 rs=[]
 for tree in ('base','candidate'):
  code=cat_code.replace("text=__import__('sys').argv[1]",f"text={text!r}")
  p=run_py(tree,code); d=json.loads(p.stdout); rs.append(d)
  f=d['fields']; print(' ',tree,'exit',p.returncode,'fields',json.dumps(f,ensure_ascii=False,sort_keys=True),'stderr',repr(p.stderr))
  if tree=='candidate':
   print('  candidate_name_exact',f.get('nombre')=='2 poltronas fijas' if id in ('MP-0004','MP-0062') else f.get('nombre') is not None,'observations_full',f.get('observaciones')==text,'no_quantity_or_stock',not any(k in f for k in ('cantidad','unidad_stock')),'only_expected_keys',set(f).issubset({'nombre','observaciones','precio_lista'}))
 print(' actual_semantic_equal',rs[0]==rs[1])
# Positive numeric count, equivalent word/labeled names, and invalid administrative fragments.
texts={
 'numeric_natural_name':'2 poltronas fijas con estructura de madera. Precio unitario de cinco mil quinientos bolivianos.',
 'word_count_legacy':'Dos poltronas fijas con estructura de madera. Precio unitario de cinco mil quinientos bolivianos.',
 'label_legacy':'Producto: 2 poltronas fijas; precio unitario de cinco mil quinientos bolivianos.',
 'measure_mm':'8 milímetros de espesor', 'measure_decimal':'2,5 metros cuadrados',
 'currency_bob':'5500 bolivianos', 'currency_code':'5500 BOB', 'currency_usd':'5500 USD',
 'zero':'0 poltronas fijas', 'negative':'-2 poltronas fijas', 'decimal_count':'2,5 poltronas fijas',
 'negated':'No quiero 2 poltronas fijas', 'negated_sin':'Sin 2 poltronas fijas',
 'admin_modelo':'Modelo 2 poltronas fijas', 'admin_precio':'Precio unitario de 2 poltronas fijas',
 'admin_stock':'Stock 2 poltronas fijas', 'admin_cantidad':'Cantidad 2 poltronas fijas',
}
for label,text in texts.items():
 vals=[]
 for tree in ('base','candidate'):
  code=cat_code.replace("text=__import__('sys').argv[1]",f"text={text!r}")
  p=run_py(tree,code);d=json.loads(p.stdout);vals.append(d)
  if tree=='candidate':
   f=d['fields']; print('CAT',label,'name',f.get('nombre'),'obs',f.get('observaciones'),'price',f.get('precio_lista'),'keys',sorted(f),'stderr',repr(p.stderr))
 print(' CAT_EQUAL',label,vals[0]==vals[1])
# CLI baselines: compare exact public JSON after stripping only latency_nlp_ms.
forms=[('mesa','Dos mesas. Precio unitario 250 bolivianos.',()),('mesa_usd','Dos mesas. Precio unitario 250 bolivianos.',('--currency','USD')),('escritorio','Un escritorio de melamina con cajones.',()),('plain_closet','Un closet de dos puertas.',()),('legacy_casilleros','Un mueble con casilleros',())]
for label,text,args in forms:
 outputs=[]
 for tree in ('base','candidate'):
  env=common.copy();env['PYTHONPATH']=str(root/tree/'src');env['TMPDIR']=str(root/'tmp')
  p=subprocess.run([str(py),'-m','homex_nlp.cli',*args,text],cwd=root/tree,env=env,text=True,capture_output=True)
  d=json.loads(p.stdout) if p.stdout else None
  if d:d.pop('latency_nlp_ms',None)
  outputs.append((p.returncode,d,p.stderr))
 print('CLI',label,'exit',outputs[0][0],outputs[1][0],'stderr_equal',outputs[0][2]==outputs[1][2],'stderr',repr(outputs[1][2]),'normalized_equal',outputs[0][1]==outputs[1][1])
