# AP6 — Adaptación comercial compatible con contrato NLP v1

`homex-nlp==0.1.0`, `schema_version=1.0` y `RULES_ONLY` permanecen sin cambios. El resultado NLP
sigue siendo evidencia/propuesta y puede contener `precio_total`; no crea productos, no elige una
variante, no calcula stock y no aprueba una proforma.

El consumidor Django incorpora el adaptador comercial **2.0**. Durante HITL, el vendedor confirma
la descripción y declara un `precio_unitario`. El adaptador no divide `precio_total / cantidad`, no
redondea el valor propuesto y no crea nuevas líneas `TOTAL_NEGOCIADO`. Los históricos que ya usan
ese modo permanecen reproducibles y de solo lectura cuando corresponda.

Esta decisión evita mutar silenciosamente el contrato público v1 y separa tres responsabilidades:

1. NLP conserva transcripción y propuesta técnica;
2. HITL recoge la decisión comercial humana;
3. PostgreSQL calcula/protege importes y aplica las reglas de aprobación.

El manifiesto verificable está en `docs/ap6-commercial-adapter-v2.json`. El corpus NER y el catálogo
comercial continúan siendo insumos separados; ningún JSONL de entrenamiento puede importarse como
producto maestro.

La ampliación futura del extractor a varios ítems, pisos, zócalos o variantes requerirá un contrato
NLP versionado nuevo y coordinación con su consumidor. AP6 no simula esa capacidad.
