#!/usr/bin/env python3
"""Audita correspondencia 1:1 entre 120 guiones, AAC y opcionalmente WAV procesados.

python3 control/validar_audios.py --listar-faltantes
python3 control/validar_audios.py --verificar-ffprobe --exigir-completos
python3 control/validar_audios.py --verificar-ffprobe --verificar-convertidos --exigir-completos
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import wave
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
FOLDERS={'muebles_pedido':'01_muebles_pedido','sillas':'02_sillas','pisos':'03_pisos','otros':'04_otros'}
MAX_BYTES=20_000_000
MAX_SECONDS=300

def checksum(path):
    digest=hashlib.sha256()
    with path.open('rb') as fd:
        for chunk in iter(lambda:fd.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()

def main():
    ap=argparse.ArgumentParser(description='Auditoría sólo lectura de grabaciones AAC y WAV generados.')
    ap.add_argument('--exigir-completos',action='store_true',help='Fallará si falta algún AAC (o WAV, si --verificar-convertidos).')
    ap.add_argument('--listar-faltantes',action='store_true')
    ap.add_argument('--verificar-ffprobe',action='store_true',help='Comprueba que los AAC realmente contienen audio AAC.')
    ap.add_argument('--verificar-convertidos',action='store_true',help='Exige WAV por ID y comprueba su SHA-256 de procedencia.')
    args=ap.parse_args()
    if args.verificar_ffprobe and not shutil.which('ffprobe'):
        print('ERROR: ffprobe no está instalado. sudo apt install ffmpeg',file=sys.stderr);return 2
    with (ROOT/'manifiesto.csv').open(encoding='utf-8-sig',newline='') as f:items=list(csv.DictReader(f,delimiter=';'))
    with (ROOT/'referencias/guiones_referencia_pregrabacion.jsonl').open(encoding='utf-8') as f:refs=[json.loads(line) for line in f]
    if len(items)!=120 or len(refs)!=120 or len({r['id'] for r in items})!=120 or {r['id'] for r in items}!={r['id'] for r in refs}:
        print('ERROR: manifiesto/referencias no coinciden o están incompletos',file=sys.stderr);return 2
    ref_by_id={r['id']:r for r in refs}
    logpath=ROOT/'evaluaciones/conversiones.csv'
    if logpath.exists():
        with logpath.open(encoding='utf-8',newline='') as f:audit={r['id']:r for r in csv.DictReader(f,delimiter=';')}
    else:audit={}
    counters=Counter();invalid=[];missing=[];unknown=[]
    expected_audio={};expected_converted={}
    for r in items:
        rid,cat=r['id'],r['categoria'];folder=FOLDERS.get(cat)
        if not folder:
            invalid.append((rid,'categoría no reconocida'));continue
        a=ROOT/folder/'audios'/f'{rid}.aac';w=ROOT/folder/'audios_asr'/f'{rid}.wav'
        expected_audio[a]=rid;expected_converted[w]=rid
        if r['audio_esperado']!=a.name or r['ruta_audio_esperada']!=a.relative_to(ROOT).as_posix() or r['ruta_audio_compatible_asr']!=w.relative_to(ROOT).as_posix() or ref_by_id[rid]['ruta_audio_esperada']!=r['ruta_audio_esperada']:
            invalid.append((rid,'desajuste en referencia/manifiesto'));continue
        if not a.exists():
            missing.append(rid);continue
        if a.is_symlink() or not a.is_file() or not (0<a.stat().st_size<=MAX_BYTES):
            invalid.append((rid,'AAC ausente, vacío, inseguro o >20 MB'));continue
        if args.verificar_ffprobe:
            p=subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=codec_name','-of','json',str(a)],capture_output=True,text=True)
            if p.returncode!=0 or not any(s.get('codec_name')=='aac' for s in json.loads(p.stdout or '{}').get('streams',[])):
                invalid.append((rid,'no se reconoció códec AAC'));continue
        counters[cat]+=1
        if args.verificar_convertidos:
            if not w.exists():
                invalid.append((rid,'WAV compatible no generado'));continue
            try:
                if w.is_symlink() or not 0<w.stat().st_size<=MAX_BYTES:raise ValueError('WAV vacío, inseguro o >20 MB')
                with wave.open(str(w),'rb') as audio:
                    duration=audio.getnframes()/audio.getframerate()
                    if (audio.getframerate(),audio.getnchannels(),audio.getsampwidth())!=(16000,1,2) or not 0<duration<=MAX_SECONDS:raise ValueError('WAV formato/duración inválidos')
                record=audit.get(rid)
                if not record or record['sha256_aac']!=checksum(a) or record['sha256_wav']!=checksum(w):raise ValueError('falta integridad entre AAC, WAV y bitácora')
                counters['wav_ok']+=1
            except Exception as exc:invalid.append((rid,str(exc)))
    for cat,folder in FOLDERS.items():
        for p in (ROOT/folder/'audios').iterdir():
            if p.is_file() and p.suffix.lower() in {'.aac','.wav','.mp3','.m4a','.ogg','.webm','.opus','.flac','.mp4'} and p not in expected_audio:
                unknown.append(str(p.relative_to(ROOT)))
        for p in (ROOT/folder/'audios_asr').iterdir():
            if p.is_file() and p.suffix.lower() in {'.aac','.wav','.mp3','.m4a','.ogg','.webm'} and p not in expected_converted:
                unknown.append(str(p.relative_to(ROOT)))
    print('===== HOMEX — AUDITORÍA DE AUDIOS AAC =====')
    print('Total de guiones/referencias:',len(items))
    print('Audios AAC encontrados y válidos:',sum(counters[c] for c in FOLDERS))
    print('IDs pendientes de AAC:',len(missing))
    print('Errores de integridad/formato/conversión:',len(invalid))
    print('Archivos no reconocidos:',len(unknown))
    if args.verificar_convertidos:print('WAV compatibles e íntegros:',counters['wav_ok'])
    for cat in FOLDERS:print(f'{cat}: {counters[cat]} / {sum(x["categoria"]==cat for x in items)} AAC')
    if args.listar_faltantes:
        for rid in missing:print('PENDIENTE',rid+'.aac')
    for rid,reason in invalid:print('ERROR',rid,reason)
    for name in unknown:print('NO_RECONOCIDO',name)
    bad=bool(invalid or unknown or (args.exigir_completos and missing))
    print('ESTADO:',('ERROR' if bad else ('COMPLETO' if not missing else 'EN PREPARACIÓN')))
    return 1 if bad else 0

if __name__=='__main__':sys.exit(main())
