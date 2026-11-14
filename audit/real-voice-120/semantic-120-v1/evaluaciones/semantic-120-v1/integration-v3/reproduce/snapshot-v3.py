import os,json,sys,pathlib
s=pathlib.Path(__file__).parent;c=json.load(open(s/'live-final-config.json'))
import django;django.setup()
from django.apps import apps
if sys.argv[1]=='authority-before.json':
 from apps.catalogo.models import Producto,ValorCatalogo
 Producto.objects.create(sku='SYNTHETIC-APPROVED-001',nombre='Synthetic approved sentinel',precio_lista='999.00',stock='0',activo=True,categoria=ValorCatalogo.objects.get(concepto__codigo='CATEGORIA_PRODUCTO',codigo='OTRO'),unidad_stock=ValorCatalogo.objects.get(concepto__codigo='UNIDAD_MEDIDA',codigo='PIEZA'))
d={}
for m in apps.get_models():
 if m._meta.app_label in ['catalogo','movimientos_stock','proformas','pedidos','ordenes_trabajo','auth','accounts']:
  fields=[f.attname for f in m._meta.concrete_fields if f.name not in ['password','last_login']]
  d[m._meta.label]=list(m.objects.order_by('pk').values(*fields))
pathlib.Path(c['out'],sys.argv[1]).write_text(json.dumps(d,default=str,sort_keys=True,indent=2))
