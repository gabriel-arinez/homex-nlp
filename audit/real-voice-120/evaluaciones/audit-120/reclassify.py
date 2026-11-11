"""Apply the seven user-confirmed category corrections without moving audio."""
import csv
import hashlib
import json
import shutil
import wave
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evaluaciones/audit-120'
IDS = {'MP-0005', 'MP-0063', 'MP-0068', 'SIL-0010', 'SIL-0019', 'SIL-0020', 'SIL-0029'}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

manifest = ROOT / 'manifiesto.csv'
with manifest.open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f, delimiter=';')
    columns = reader.fieldnames
    rows = list(reader)
refs_path = ROOT / 'referencias/guiones_referencia_pregrabacion.jsonl'
refs = [json.loads(l) for l in refs_path.read_text().splitlines()]
trace = [json.loads(l) for l in (ROOT / 'referencias/trazabilidad_fuentes.jsonl').read_text().splitlines()]
assert len(rows) == len(refs) == len(trace) == 120
assert len({r['id'] for r in rows}) == 120
assert {r['id'] for r in rows} == {r['id'] for r in refs} == {r['id'] for r in trace}
assert IDS <= {r['id'] for r in rows}
ledger = []
for row, ref in zip(rows, refs):
    assert row['id'] == ref['id']
    entry = {'id': row['id'], 'audio': {}}
    for key in ['ruta_audio_esperada', 'ruta_audio_compatible_asr']:
        assert row[key] == ref[key]
        p = ROOT / row[key]
        assert p.is_file() and not p.is_symlink()
        entry['audio'][key] = {'path': row[key], 'sha256': digest(p), 'bytes': p.stat().st_size}
    with wave.open(str(ROOT / row['ruta_audio_compatible_asr'])) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 16000)
        entry['duration_seconds'] = w.getnframes() / w.getframerate()
    ledger.append(entry)
backup = OUT / 'before-reclassification'
backup.mkdir(exist_ok=False)
paths = [manifest, refs_path, ROOT / 'control/RESUMEN.json', ROOT / 'README.md']
for p in paths:
    dest = backup / p.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
changes = []
for row, ref in zip(rows, refs):
    if row['id'] in IDS:
        assert row['categoria'] == ref['categoria']
        changes.append({'id':row['id'], 'before':row['categoria'], 'after':'OTRO',
                        'source':ref['archivo_origen'], 'source_records':ref['registros_fuente'],
                        'title':ref['titulo_fuente'], 'reason':'User-confirmed commercial category correction, including office sillones'})
        row['categoria'] = ref['categoria'] = 'OTRO'
for row, ref in zip(rows, refs):
    if row['categoria'] == 'otros':
        row['categoria'] = ref['categoria'] = 'OTRO'
with manifest.open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=columns, delimiter=';')
    writer.writeheader()
    writer.writerows(rows)
refs_path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in refs))
summary_path = ROOT / 'control/RESUMEN.json'
summary = json.loads(summary_path.read_text())
summary.update(guiones_por_categoria=dict(Counter(r['categoria'] for r in refs)),
               audios_presentes=120, convertidos_presentes=120,
               estado='AUDIOS_VERIFICADOS_CLASIFICACION_CORREGIDA',
               reclasificacion='evaluaciones/audit-120/reclassification.json')
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
with (ROOT / 'README.md').open('a') as f:
    f.write('\n## Commercial classification correction — 2026-11-11\n\n'
            'Current evaluation categories: 76 muebles_pedido, 27 sillas, 7 pisos, 10 OTRO. '
            'Folder names, historical reading documents, IDs and audio paths are unchanged; '
            'use manifiesto.csv as the authoritative routing index, not the folder or ID prefix. '
            'Seven sillón records were reclassified with user confirmation, including office chairs. '
            'See evaluaciones/audit-120/reclassification.json and before-reclassification/ for exact history.\n')
for entry in ledger:
    for audio in entry['audio'].values():
        assert digest(ROOT / audio['path']) == audio['sha256']
(OUT / 'audio-ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+'\n')
(OUT / 'reclassification.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'count':len(refs),'categories':summary['guiones_por_categoria'],'changes':changes,
                  'audio_integrity':'240 hashes unchanged','total_duration_s':sum(e['duration_seconds'] for e in ledger)},ensure_ascii=False,indent=2))
