import json,os,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]); cwd=Path('/home/gabriel/HOMEX/homex-nlp'); py=cwd/'.venv/bin/python'; env0=os.environ.copy()
cli_forms=[
 ('legacy_casilleros','Un mueble con casilleros'),
 ('mesa','Dos mesas. Precio unitario 250 bolivianos.'),
 ('escritorio','Un escritorio de melamina con cajones.'),
 ('closet','Un closet de dos puertas.'),
 ('negated_closet','No quiero un armario.'),
 ('independent_products','Un armario y una mesa.'),
 ('singular_casillero','Un casillero para archivo.'),
 ('plural_casilleros','Dos casilleros para archivo.'),
]
def call(tree,form,extra=()):
 env=env0.copy(); env['PYTHONPATH']=str(root/tree/'src'); env['TMPDIR']=str(root/'tmp'); p=subprocess.run([str(py),'-m','homex_nlp.cli',*extra,form],cwd=root/tree,env=env,text=True,capture_output=True)
 d=json.loads(p.stdout) if p.stdout.strip() else None
 if d: d.pop('latency_nlp_ms',None)
 return p.returncode,d,p.stderr
for name,form in cli_forms:
 b=call('base',form); c=call('candidate',form)
 print('CLI',name,'exit',b[0],c[0],'stderr',repr(b[2]),repr(c[2]),'equal',b[1]==c[1])
 for label,result in [('base',b[1]),('candidate',c[1])]:
  proposal=result.get('item_proposal') if result else None
  print(' ',label,'type=',proposal and proposal.get('item_type'),'name=',proposal and proposal.get('name'),'qty=',proposal and proposal.get('quantity'),'status=',result and result.get('status'),'unresolved=',proposal and proposal.get('unresolved'))
# Direct catalog tests for floor HDF interpretations.
script=r'''from homex_nlp.catalog import CatalogRequest,extract_catalog
import json,sys
for label,text in [
 ('hdf_number_words','Piso flotante HDF de ocho milímetros.'),
 ('hdf_digit','Piso flotante HDF de 8 mm.'),
 ('hdf_explicit_other_axis','Piso flotante HDF de 8 mm de ancho.'),
 ('hdf_alternative','Piso flotante HDF de ocho o diez milímetros.'),
 ('hdf_negated','Piso flotante sin HDF de ocho milímetros.'),
 ('hdf_size_pair','Piso flotante HDF de 8 por 20 mm.'),
 ('measurement_legacy','Piso flotante de 8 milímetros de espesor.'),
]:
 r=extract_catalog(CatalogRequest(category='PISO_FLOTANTE',text=text)); print(label,json.dumps({'espesor_mm':r.fields.get('espesor_mm'),'largo_mm':r.fields.get('largo_mm'),'unrecognized':r.unrecognized},ensure_ascii=False))
'''
for tree in ('base','candidate'):
 env=env0.copy();env['PYTHONPATH']=str(root/tree/'src');env['TMPDIR']=str(root/'tmp')
 p=subprocess.run([str(py),'-c',script],cwd=root/tree,env=env,text=True,capture_output=True,check=True)
 print('FLOOR',tree);print(p.stdout,end='')
