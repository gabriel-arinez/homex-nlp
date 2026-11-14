import csv, json, os, pathlib, secrets, shutil, socket
s=pathlib.Path(os.environ['HOMEX_REPRO_SCRATCH'])
corpus=pathlib.Path(os.environ['HOMEX_REPRO_CORPUS']).resolve()
out=s/'evidence'; out.mkdir(exist_ok=False)
ports=[]
for _ in range(3):
 with socket.socket() as sock:
  sock.bind(('127.0.0.1',0)); ports.append(sock.getsockname()[1])
cfg=dict(pgport=ports[0],apiport=ports[1],frontport=ports[2],username='audit-live-synthetic',password=secrets.token_urlsafe(24),out=str(out),samples={},django_secret=secrets.token_urlsafe(48))
audio=s/'live-audio'; audio.mkdir(exist_ok=False)
for row in csv.DictReader((corpus/'manifiesto.csv').open(encoding='utf-8-sig'),delimiter=';'):
 if row['id'] in ['MP-0001','SIL-0001','PIS-0001','MP-0005','MP-0036','MP-0045','MP-0067','PIS-0006']:
  target=audio/(row['id']+'.wav'); shutil.copyfile(corpus/row['ruta_audio_compatible_asr'],target); cfg['samples'][row['id']]=str(target)
assert len(cfg['samples']) == 8, 'All eight audio cases are required'
(s/'live-final-config.json').write_text(json.dumps(cfg)); os.chmod(s/'live-final-config.json',0o600)
(s/'audit_live_settings.py').write_text("""from config.settings.test import *
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:%d']
CELERY_BROKER_URL = 'memory://'
""" % ports[2])
print('Own loopback ports selected; synthetic credentials generated without disclosure.')
