# HOMEX Corpus 2.0.0-rc.2 — candidato experimental pasivo

Archivo histórico y desarrollo separados. No es gold humano ni benchmark de voz.

Reconstruir: `uv run --locked --extra dev python -m training.corpus_v2_rc2.build --output /tmp/homex-rc2-a`.
Validar: `uv run --locked --extra dev python -m training.corpus_v2_rc2.validate /tmp/homex-rc2-a`.
Gate CI: `uv run --locked --extra dev python -m training.corpus_v2_rc2.ci_gate --evidence /tmp/homex-rc2-ci`.
No entrenar ni copiar sobre las rutas V1. Desactivar el candidato constituye rollback; V1 no cambia.

## Política de independencia

`source_case_id` = diseño comercial concreto; `paraphrase_group_id` = transformaciones del caso;
`template_id` = plantilla específica, no familia de mobiliario; `scenario_family_id` = contexto descriptivo, solo alerta.
Una coincidencia de fuente/caso/paráfrasis/plantilla, huella con números/unidades/acentos normalizados,
o referencia estructurada equivalente impone una partición. Prefijos y vocabulario común solos no.
Los pares de lenguaje parcial se reportan como alertas de baja confianza con decisión explícita;
no se proclama independencia universal frente a paráfrasis que estos detectores no reconozcan.

Los 675 V1 se conservan byte por byte con sus splits 483/94/98 en archive_v1; sidecar rc1 separado.
Se retienen 52 casos rc1 sin padres V1 explícitos; su independencia es técnica, no certificación humana.
Nuevas recetas cubren únicamente brechas comprobadas de etiquetas y tareas distintas.
No se reserva holdout sintético: escenarios escasos se destinan a train/dev.
external_human_gold tiene cero muestras; adquirir fuentes y hablantes consentidos independientes.

## Límites

Tamaño efectivo por etiqueta se mide en grupos, no en número de paráfrasis. EXPERIMENTAL_READY
solo significa que puede diseñarse un experimento offline limitado; no precisión predictiva,
homologación comercial ni permiso para entrenar en este encargo.
Estados separados: integridad de formato, coherencia técnica inferida y revisión humana independiente.

Las 24 etiquetas permanecen intactas. APOYABRAZOS/CABECERA/ERGONOMIA/SOPORTE_LUMBAR se aplican
a sillas; CLASE_RESISTENCIA a pisos. No se obliga a esas etiquetas en familias inadecuadas.
Cantidad interna/capacidad siguen como relaciones, nunca nuevas clases NER. Precios se validan
con Decimal; moneda de Condiciones no se inventa; no convertir precios ni metros a barras.
Los 120 ítems privados y cuatro referencias parciales no entran en supervisión.

## Revisión real

review/kit.csv y kit.jsonl permiten adjudicación por campo con texto sintético, evidencia,
alternativa, prioridad y campos vacíos de revisor/fecha/decisión. Usar el importador explícito;
ningún generador asigna HUMAN_REVIEWED o GOLD_ELIGIBLE. Véase review/GUIDE.md.
