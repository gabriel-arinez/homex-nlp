# V16 RULES_ONLY — candidato de mejora, sin promoción automática

Base auditada: PR #37, `40719cca646f314ec287fb2c68fa3e2667aa59ed`.
Paquete 0.1.16, `prf04-rules-v16`, contrato público 1.0 sin cambios.

## Cambios funcionales

- Familia comercial: palabras completas y contexto de pedido sustituyen el veto
  global de subcadenas silla/piso. Las menciones espaciales y secundarias ya no
  invalidan automáticamente un mueble; pedidos independientes siguen fuera de voz.
- Precios: todas las menciones explícitas conservan evidencia; rectificaciones
  inequívocas sustituyen importes, negativos y alternativas exigen revisión.
  Modalidades unitario/total explícitas pueden corroborarse si coinciden exactamente.
  Decimal continúa siendo la única aritmética monetaria; la referencia aproximada
  del contrato histórico sigue sin convertirse en precio efectivo.
  Su redondeo HALF_UP coincide con el validador, incluso en empates a seis decimales.
- Componentes: laterales sustantivos, calificadores interiores/laterales/abatibles,
  cantidades internas, herrajes vinculados al ámbito y espesores diferenciados.
  No se añaden relaciones padre-hijo ni códigos de catálogo.
- Medidas: precisión decimal dimensional independiente del lector monetario,
  espesores en palabras y sustituciones explícitas con evidencia cancelada.
- Atributos: alternativas de color/material quedan pendientes; «madera clara»
  no genera material madera. Atributos de piezas excluidas no pasan al ámbito general.
- Oralidad: nombres con calificadores controlados, uno, precios enteros en palabras,
  descuento cero explícito y anulaciones de pedidos. No se reconstruye texto ASR.

Los cambios en tests anteriores sólo actualizan identificadores de versión y el
nombre literal de repisas laterales; corpus, splits, referencias y tests V1 no se editan.
La batería nueva deriva de requisitos independientes y no de IDs o textos holdout.

## Evaluación y límites

Se reutiliza sin cambios el protocolo `training.decision_nlp`: mismos 103 textos,
referencias y denominadores. Histórico legado 6/16 → 7/16; guiones integrales
0/20 → 5/20. No son referencias humanas del audio. El holdout interno conocido
permanece 0/5; FP críticos 18 → 19 y FN 77 → 79. No se presenta como prueba ciega.
Las cifras completas y las salidas individuales se conservan en el expediente privado.
La mayor recuperación en guiones no acredita generalización ni autoriza fabricación.

La promoción queda **retenida**: conservar V15 hasta resolver/adjudicar las
regresiones comerciales y completar la homologación funcional. Los PRs son
candidatos revisables; no implican merge ni despliegue. No hay cambio ASR ni NER.

## Reproducir

```bash
uv sync --locked --extra dev
make check
make distribution-check
uv audit --locked
PYTHONPATH=src:. uv run --locked --extra dev python -m tools.evaluate_rules_release \
  --inputs /ruta/privada/evaluation_inputs.jsonl --output /ruta/nueva/resultados.json
uv run --locked --extra dev python tools/verify_rules_release.py /ruta/privada/expediente
```

La evaluación usa el proyector offline histórico para conservar comparabilidad;
se contrasta adicionalmente con adaptador, proyector y validador Django reales
sobre PostgreSQL nuevo. Las pruebas de editor Vue conservan cancelaciones,
respuestas tardías, cambios manuales y cálculo exacto. El flujo WAV real usa
pipeline directo: no acredita latencia Celery ni recorrido navegador completo.
