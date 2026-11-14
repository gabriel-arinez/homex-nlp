#!/usr/bin/env python3
"""Valida cobertura de grabaciones HOMEX; solo lectura, no modifica archivos.

Uso: python control/validar_audios.py [--exigir-completos] [--listar-faltantes] [--verificar-ffprobe]
"""
import argparse
import csv
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

EXTS={'.wav','.webm','.m4a','.ogg','.opus','.mp3','.flac','.mp4'}
ROOT=Path(__file__).resolve().parent.parent
FOLDERS={'muebles_pedido':'01_muebles_pedido','sillas':'02_sillas','pisos':'03_pisos','otros':'04_otros'}

def main():
    ap=argparse.ArgumentParser(description='Verifica audios de grabación de HOMEX sin alterar contenidos.')
    ap.add_argument('--exigir-completos',action='store_true',help='Código de salida no cero si falta cualquier audio.')
    ap.add_argument('--listar-faltantes',action='store_true',help='Muestra uno a uno los IDs pendientes.')
    ap.add_argument('--verificar-ffprobe',action='store_true',help='Verifica legibilidad multimedia usando ffprobe instalado.')
    args=ap.parse_args()
    with (ROOT/'manifiesto.csv').open(encoding='utf-8-sig',newline='') as fd:
        items=list(csv.DictReader(fd,delimiter=';'))
    seen={r['id'] for r in items}
    assert len(items)==120 and len(seen)==120, 'Manifiesto incompleto o con IDs repetidos'
    found={};missing=[];duplicates=[];unrecognized=[];invalid=[];by=Counter()
    for row in items:
        rid,cat=row['id'],row['categoria']
        audio_dir=ROOT/FOLDERS[cat]/'audios'
        matches=sorted(p for p in audio_dir.iterdir() if p.is_file() and p.stem==rid and p.suffix.lower() in EXTS)
        if not matches:missing.append(rid)
        elif len(matches)>1:duplicates.append((rid,[p.name for p in matches]))
        else:
            p=matches[0];found[rid]=p;by[cat]+=1
            if p.stat().st_size==0:invalid.append((rid,'archivo vacío'))
            elif args.verificar_ffprobe:
                if shutil.which('ffprobe') is None:
                    raise RuntimeError('ffprobe no está instalado; vuelva a ejecutar sin --verificar-ffprobe')
                result=subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=codec_name','-of','default=noprint_wrappers=1',str(p)],capture_output=True,text=True)
                if result.returncode!=0 or 'codec_name=' not in result.stdout:invalid.append((rid,result.stderr.strip() or 'no se detectó códec de audio'))
    for cat,folder in FOLDERS.items():
        for p in (ROOT/folder/'audios').iterdir():
            if p.is_file() and p.suffix.lower() in EXTS and (p.stem not in seen or p.stem not in {r['id'] for r in items if r['categoria']==cat}):
                unrecognized.append(str(p.relative_to(ROOT)))
    print('===== HOMEX / AUDITORÍA DE GRABACIONES =====')
    print(f'Guiones esperados: {len(items)}')
    print(f'Audios encontrados (un archivo válido por ID): {len(found)}')
    print(f'IDs faltantes: {len(missing)}')
    print(f'IDs con archivos duplicados: {len(duplicates)}')
    print(f'Archivos desconocidos o fuera de carpeta: {len(unrecognized)}')
    print(f'Archivos vacíos o inválidos: {len(invalid)}')
    for cat in FOLDERS:print(f'{cat}: {by[cat]} / {sum(x["categoria"]==cat for x in items)}')
    if args.listar_faltantes:
        for rid in missing:print('FALTA',rid)
    for rid,files in duplicates:print('DUPLICADO',rid,files)
    for fname in unrecognized:print('NO_RECONOCIDO',fname)
    for rid,err in invalid:print('INVALIDO',rid,err)
    print('ESTADO:', 'COMPLETO' if not(missing or duplicates or invalid or unrecognized) else 'INCOMPLETO')
    if args.exigir_completos and (missing or duplicates or invalid or unrecognized):return 1
    return 0

if __name__=='__main__':sys.exit(main())
