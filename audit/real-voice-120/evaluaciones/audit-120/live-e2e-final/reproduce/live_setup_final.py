import csv, json, os, pathlib, secrets, shutil, socket
s=pathlib.Path(__file__).parent
corpus=pathlib.Path('/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz')
out=corpus/'evaluaciones/audit-120/live-e2e-final'; out.mkdir(parents=True,exist_ok=True)
ports=[]
for _ in range(3):
 with socket.socket() as sock:
  sock.bind(('127.0.0.1',0)); ports.append(sock.getsockname()[1])
cfg=dict(pgport=ports[0],apiport=ports[1],frontport=ports[2],username='audit-live-synthetic',password=secrets.token_urlsafe(24),out=str(out),samples={})
audio=s/'live-audio'; audio.mkdir(exist_ok=True)
for row in csv.DictReader((corpus/'manifiesto.csv').open(encoding='utf-8-sig'),delimiter=';'):
 if row['id'] in ['MP-0001','SIL-0001','PIS-0001','MP-0005']:
  target=audio/(row['id']+'.wav'); shutil.copyfile(corpus/row['ruta_audio_compatible_asr'],target); cfg['samples'][row['id']]=str(target)
(s/'live-final-config.json').write_text(json.dumps(cfg)); os.chmod(s/'live-final-config.json',0o600)
(s/'backend/audit_live_settings.py').write_text("""from config.settings.test import *
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:%d']
CELERY_BROKER_URL = 'memory://'
""" % ports[2])
print('Own loopback ports selected; synthetic credentials generated without disclosure.')
