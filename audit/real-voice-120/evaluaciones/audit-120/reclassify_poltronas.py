"""Apply the three explicitly confirmed poltrona corrections; preserve history."""
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evaluaciones/audit-120'
IDS={'MP-0004','MP-0062','MP-0067'}
backup=OUT/'before-poltronas'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def audio_unchanged():
    ledger=json.loads((OUT/'audio-ledger.json').read_text())
    assert len(ledger)==120
    for row in ledger:
        for entry in row['audio'].values():
            p=ROOT/entry['path']
            assert p.is_file() and not p.is_symlink()
            assert digest(p)==entry['sha256']
    return 240

assert audio_unchanged()==240
manifest=ROOT/'manifiesto.csv'
with manifest.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f,delimiter=';');columns=reader.fieldnames;rows=list(reader)
p=ROOT/'referencias/guiones_referencia_pregrabacion.jsonl'
refs=[json.loads(line) for line in p.read_text().splitlines()]
ref_by_id={r['id']:r for r in refs}
assert len(rows)==len(refs)==len(ref_by_id)==120
assert len({r['id'] for r in rows})==120
assert {r['id'] for r in rows}==set(ref_by_id)
assert IDS <= set(ref_by_id)
for id in IDS:
    assert ref_by_id[id]['categoria']=='muebles_pedido'
    assert 'poltrona' in ref_by_id[id]['titulo_fuente'].casefold()
backup.mkdir(exist_ok=False)
for rel in ['manifiesto.csv','referencias/guiones_referencia_pregrabacion.jsonl',
            'control/RESUMEN.json','README.md','evaluaciones/audit-120/reclassification.json',
            'evaluaciones/audit-120/progress-report.md','evaluaciones/audit-120/root-cause-matrix.json',
            'evaluaciones/audit-120/root-cause-matrix.csv']:
    source=ROOT/rel;dest=backup/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
changes=json.loads((OUT/'reclassification.json').read_text())
assert len(changes)==7
for row in rows:
    id=row['id'];ref=ref_by_id[id]
    assert row['categoria']==ref['categoria']
    if id not in IDS:continue
    changes.append({'id':id,'before':ref['categoria'],'after':'OTRO',
                    'source':ref['archivo_origen'],'source_records':ref['registros_fuente'],
                    'title':ref['titulo_fuente'],
                    'reason':'User explicitly confirmed poltronas as OTRO: si, tambien deben clasificarse como OTRO'})
    row['categoria']=ref['categoria']='OTRO'
counts=dict(Counter(r['categoria'] for r in refs))
assert counts=={'muebles_pedido':73,'OTRO':13,'sillas':27,'pisos':7}
with manifest.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=columns,delimiter=';');writer.writeheader();writer.writerows(rows)
p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in refs))
p=ROOT/'control/RESUMEN.json';summary=json.loads(p.read_text());summary['guiones_por_categoria']=counts
summary['reclasificacion']='evaluaciones/audit-120/reclassification.json'
summary['confirmacion_poltronas']='si, tambien deben clasificarse como OTRO'
p.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(OUT/'reclassification.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
p=ROOT/'README.md';text=p.read_text();text=text.replace('76 muebles_pedido, 27 sillas, 7 pisos, 10 OTRO','73 muebles_pedido, 27 sillas, 7 pisos, 13 OTRO')
text=text.replace('Seven sillón records were reclassified with user confirmation, including office chairs.','Ten records were reclassified with user confirmation: seven sillones (including office chairs) and three poltronas fijas. Historical evaluation snapshots retain their original categories; evaluaciones/audit-120/latest-evaluation.json identifies the current corrected routing.')
p.write_text(text)
# Compare every input field other than category against the backup.
old_refs=[json.loads(line) for line in (backup/'referencias/guiones_referencia_pregrabacion.jsonl').read_text().splitlines()]
for old,new in zip(old_refs,refs):
    assert {k:v for k,v in old.items() if k!='categoria'}=={k:v for k,v in new.items() if k!='categoria'}
    assert old['categoria']==new['categoria'] or old['id'] in IDS
print(json.dumps({'counts':counts,'total':len(refs),'newly_changed_ids':sorted(IDS),
                  'total_commercial_reclassifications':len(changes),'audio_hashes_unchanged':audio_unchanged(),
                  'guion_text_and_all_noncategory_reference_fields':'UNCHANGED'},ensure_ascii=False,indent=2))
