import os,time,django
django.setup()
from apps.capturas.outbox import publicar_pendientes
while True:
 result=publicar_pendientes()
 if result['publicados'] or result['errores']: print(result,flush=True)
 time.sleep(.5)
