# Matriz formal del plan maestro — 27-10-2026

Estado por gates; sin ponderaciones ni porcentajes. Cumplido significa evidencia
acotada al criterio indicado, no cierre completo de etapa ni autorización de promoción.
La base de esta entrega es 449a5cf; otros commits se citan como entregas separadas.

| Etapa | Estado | Criterios acreditados | Criterios pendientes | Artefactos/evidencias | Bloqueo o dependencia |
|---|---|---|---|---|---|
| 1. Auditoría integral | PARCIAL / continuidad | Corpus V1 censado; fuentes y entregas anteriores localizadas; riesgos de plantilla y origen delimitados | Consolidación 1A–1E de tres repos, trazas E2E actuales, reconciliación comercial y aprobación global | `audit.json`, README, continuidad 25/26-10; commits de PRs #20–28 | Fuera del alcance exclusivo NLP: responsables de integración y dominio |
| 2. Baseline y medición | PARCIAL | V1 675 y splits sellados conservados; hashes de 12 archivos; dev diagnóstico, entorno/configuración y p50/p95 extractor | Test externo independiente, baseline humano, CPU/RAM de flujo, cold/warm ASR/E2E, umbrales acordados | `audit.json`, `dev_experiment.json`, `training.json`, `audio_inventory.json` | Sesiones/reference válidas, hardware/operador E2E y decisiones HOMEX |
| 3. Curación documental V2 | PARCIAL | Integridad mecánica 675; overlay reversible de 577 train/dev; 49 parches literales y hechos con evidencia; TXT local cotejado por SHA; propuestas V2 previas inventariadas | Procedencia por ítem; revisión de 675 por custodio sin revelar test; adjudicación de expected/ambigüedades; homologación de cambios rc.1/rc.2 | `development_overlay.json`; #20/#22 y sus kits; `audit.json` | Especialista comercial, registro de revisores, enlaces documentales y aprobación de ambigüedades |
| 4. Corpus oral/melamina | PARCIAL | Estructura vacía y esquema estricto reproducibles; separación origen; límites de padre/grupo/hablante/sesión; pruebas de privacidad, spans y fugas | Corpus oral revisado, cobertura por fenómeno y dominio, independencia semántica, adjudicación de negaciones/ámbitos; evaluación del piloto 48 | `oral_intake/`, `training/closure_v2/oral.py`, tests; rc.2 previo con 66 sintéticos | Revisores y nuevos diseños/casos válidos; no llenar cuotas con ficción etiquetada REAL |
| 5. Ingesta y voz real | PARCIAL | 20 WAV piloto conocido validados SHA/tamaño/PCM en lectura; procedimiento por lote y controles; herramienta de escucha humana previa identificada | Consentimientos verificables, retención/custodia, transcripciones fieles aprobadas, enlace con intentos, anotación comercial y test externo independiente | `audio_inventory.json`, `oral_intake/PROCEDIMIENTO.md`, #26/#28 | Custodio y humanos que escuchen; datos privados fuera de esta rama. WER no evaluable |
| 6. Reglas/NER/híbrido | PARCIAL / diagnóstico | Entrenamiento seed 404/10 épocas, 262 train/62 dev; comparación A v6/B existente, P/R/F1 por etiqueta y micro/macro, latencia y contrato; experimento rc.2/v13/C previo inventariado | D2–D5, ablations justificadas, errores/relaciones/JSON con referencias válidas, variabilidad, dev humano, test externo final; comparación actualizada con runtime candidato | `dev_experiment.json`, `training.json`; #24 `4c94a75`; código reproducible | Datos homologados, revisión dominio y criterio predeclarado. F1 sintético no habilita promoción |
| 7. Integración/optimización | PENDIENTE en esta entrega / frente separado | Runtime/contrato/V1 de esta base preservados; alcance separado del PR #30 | Integración del candidato vigente con backend/frontend; E2E, cola, carga ASR, retención, persistencia y no regresión comercial actuales | Históricos en continuidad; esta rama solo gates NLP | Agente integrador y aprobación expresa para integración. No merge/deploy en este encargo |
| 8. Validación externa/cierre académico | PENDIENTE | Amenazas a validez, denominadores, limitaciones y reproducción documentados | WER/F1 externos legítimos, productividad, múltiples vendedores/casos, revisión HOMEX, CI e integración finales, release/rollback aprobados | README, matriz, informes de diagnóstico separados por naturaleza | Estudio de campo y aprobación humana. Ninguna etapa declarada completa |

## Criterios transversales que bloquean promoción

1. `human_gold=false`, WER sin calcular, holdout externo disponible cero.
2. Referencias actuales del experimento son preanotación sintética; fuentes
   documentales no reconcilian automáticamente 675 ítems reales.
3. Cero cruces por IDs no demuestra ausencia de fuga por plantilla o semántica.
4. Validar contrato no prueba exactitud comercial ni guardado integral.
5. Los gates locales solo acreditan los comandos realmente ejecutados. El estado
   remoto y CI de esta nueva entrega deben consultarse en su PR; no se heredan
   resultados verdes de otros commits.
