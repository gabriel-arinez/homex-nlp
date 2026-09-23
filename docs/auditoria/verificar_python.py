"""Auditoría reproducible; no modifica el dataset ni la SQLite del proyecto.
Ejecutar: backend/.venv/bin/python docs/auditoria/verificar_python.py
"""
import collections
import json
import logging
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
import spacy
import database
from convert_to_spacy import LABELS_VALIDOS, registros_a_ejemplos_spacy
from nlp_engine import MotorNLP, DetalleMueble
logging.getLogger().setLevel(logging.ERROR)

rows = [json.loads(line) for line in (ROOT / 'data/dataset.jsonl').read_text().splitlines() if line.strip()]
labels = collections.Counter()
invalid, overlaps, misaligned = [], [], []
nlp = spacy.blank('es')
for i, row in enumerate(rows, 1):
    text, spans = row['text'], row['label']
    doc = nlp.make_doc(text)
    for start, end, label in spans:
        labels[label] += 1
        if not 0 <= start < end <= len(text):
            invalid.append([i, start, end, label])
        elif doc.char_span(start, end, alignment_mode='strict') is None:
            misaligned.append([i, start, end, label, text[start:end]])
    for a, b in zip(sorted(spans), sorted(spans)[1:]):
        if a[1] > b[0]:
            overlaps.append([i, a, b])
examples = registros_a_ejemplos_spacy(rows, nlp)
engine = MotorNLP(str(ROOT / 'data/modelos_entrenados/model-best'))
probes = [
    'Escritorio de melamina de 18 mm, 1.80 metros de ancho y 0.80 metros de alto. cantidad 2. total 1700',
    'Un escritorio de melamina color nogal y dos veladores blancos',
    'total 1,500.00', 'total 1.500 Bs', 'sin datos', 'dos escritorios de melamina',
]
results = {
    'spacy_version': spacy.__version__,
    'records': len(rows), 'annotations': sum(labels.values()), 'labels': dict(labels),
    'invalid_offsets': invalid, 'overlaps': overlaps,
    'strict_token_misalignment': misaligned,
    'exact_duplicate_texts': len(rows) - len({r['text'] for r in rows}),
    'converter_current_entities': sum(len(e.reference.ents) for e in examples),
    'labels_rejected_after_key_fix': {k:v for k,v in labels.items() if k not in LABELS_VALIDOS},
    'model_path_exists': Path(engine.ruta_modelo).exists(),
    'active_pipeline': engine.nlp.pipe_names,
    'probes': [engine.procesar_cotizacion(t).model_dump() for t in probes],
    'negative_values_accepted': DetalleMueble(cantidad=-2, precio_total=-10).model_dump(),
    'empty_metrics': database._calcular_metricas_item({}, {}),
    'order_only_metrics': database._calcular_metricas_item({'accesorios':['a','b']}, {'accesorios':['b','a']}),
    'material_spans': dict(collections.Counter(r['text'][s:e] for r in rows for s,e,l in r['label'] if l=='MATERIAL')),
    'products': dict(collections.Counter(r['text'][s:e] for r in rows for s,e,l in r['label'] if l=='PRODUCTO')),
}
with tempfile.TemporaryDirectory(prefix='homex-audit-sqlite-') as tmp:
    database.DB_PATH = str(Path(tmp) / 'audit.db')
    database.init_db()
    payload = dict(captura_id=999,items_ia_ids=[777],muebles_ia=[{'producto':'Falso'}],muebles_humano=[{'producto':'Falso'}],latencia_total_ms=1,latencia_asr_ms=1,latencia_nlp_ms=1,labels_encontrados=[])
    results['nonexistent_capture_hitl'] = database.guardar_validacion_hitl(**payload)
    database.guardar_validacion_hitl(**payload)
    with sqlite3.connect(database.DB_PATH) as conn:
        results['duplicate_hitl_rows'] = conn.execute('SELECT COUNT(*) FROM metricas_pipeline WHERE captura_id=999').fetchone()[0]
    results['deleted_item_metrics'] = database.guardar_validacion_hitl(**{**payload,'muebles_humano':[]})
output = ROOT / 'docs/auditoria/resultados_python.json'
output.write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: results[k] for k in ['records','annotations','strict_token_misalignment','converter_current_entities','material_spans','nonexistent_capture_hitl','duplicate_hitl_rows','deleted_item_metrics']},ensure_ascii=False,indent=2))
