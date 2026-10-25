# HOMEX — Línea base 02 / checkpoint reproducible previo a correctivos P0

Fecha de referencia: 2026-10-24 (America/La_Paz). Estado: baseline documental, **no entrenamiento** ni certificación de métricas.

## Repositorios auditados, rama `feat/prf04-voz-configurador`

| Repositorio | Commit SHA original | Estado |
| --- | --- | --- |
| homex-nlp | `449a5cf34db2202bdb27aed74c61923ea3176dde` | Origen inmutable de los correctivos |
| homex-backend | `8f6fed352e8e49f819884e9db7ffb1d24f355ca7` | No actualizado por este correctivo |
| homex-frontend | `554f382e40533ed16c462c9048482c487e603aad` | No actualizado por este correctivo |

Los tres repositorios estaban sincronizados con origin en el diagnóstico local del usuario, sin cambios rastreados. Backend presentaba únicamente `celerybeat-schedule.db` sin seguimiento. Ningún comando destructivo ni modificación a los repositorios locales del usuario.

## Corpus NLP V1 protegido (675 registros, 300 proformas agrupadas)

| Fuente | Filas | SHA-256 |
| --- | ---: | --- |
| `data/corpus/muebles_pedido.jsonl` | 380 | `5c8d51d4794c8e8b2eef6a450d226a8479f95365b35456eb9c1fa7d036f12315` |
| `data/corpus/sillas.jsonl` | 101 | `1d626cfa64e42d1569f8262d8f255ae788e4d72ee3a150c0c5f98212df735b68` |
| `data/corpus/pisos_flotantes.jsonl` | 97 | `2762fc4be08ef13d62da4e513d43e33aeed21e66b1815cd41ad857ef1ede919a` |
| `data/corpus/otros_productos.jsonl` | 97 | `bbe851818072e7d86eb0c8a13b7594df7f57bfdcf9e4ea2c47c8fcfb400eae87` |

Splits sellados: `data/splits/{muebles_pedido,sillas,pisos_flotantes,otros_productos}.json`. No alterar texto, offsets, hash ni particiones de la línea base; crear V2 por separado. Referencias esperadas generadas desde anotaciones, **no gold humano revisado**.

## Entornos y contratos originales

- Wheel operativo NLP `homex_nlp-0.1.5-py3-none-any.whl`, SHA-256 `ccf0b0d87af865faa51ee23d6857565e26599d3b28a52c3a55193e8c5742965f`.
- Python local NLP/backend 3.11.15; spaCy 3.8.13, faster-whisper 1.2.1, ctranslate2 4.8.2.
- Django 5.2.17, Celery 5.5.3; PostgreSQL y Redis disponibles en el diagnóstico; API HTTP no iniciada en ese momento.
- OpenAPI backend/frontend idéntico SHA-256 `aae8c03d2d3a017dbfc9a9c7afdfe9f81f437dc9cf408bb0cee4bb9a98d35fdd`.
- Motor operativo `RULES_ONLY`, reglas `prf04-rules-v6`, contrato NLP v1.
- Capturas 211–214 (n=4): media worker 4,797 s, ASR 3,776 s, NLP 3,25 ms; creación→publicación outbox 1,637 s. **No mide** p95, experiencia stop→formulario ni tiempo de carga ASR.

## Gates de CI pendientes (evidencia original, no ocultar)

- NLP: https://github.com/gabriel-arinez/homex-nlp/actions/runs/40084946736
- Backend: https://github.com/gabriel-arinez/homex-backend/actions/runs/40084949546
- Frontend: https://github.com/gabriel-arinez/homex-frontend/actions/runs/40084951872

El workflow frontend de integración real estaba fijado al backend histórico `42cae4102511f9646b23382233c8d0c23ebfc78c`, no al backend auditado; no atribuir automáticamente el fallo a la versión actual. El fixture del CI es TTS eSpeak, **no voz humana gold**.

## Correctivos adelantados después de este checkpoint

Este documento marca **el estado previo** a cualquier cambio de semántica de negaciones/rectificaciones. Los parches requieren pruebas de regresión, revisión de efectos en backend y frontend, publicación de wheel nuevo antes de integración y nuevos contratos solo si son necesarios. Los resultados de versiones posteriores no sustituyen las métricas originales ni permiten promocionar NER.

Pendientes del conjunto completo de Etapa 2: evaluación independiente humana, benchmark en hardware real, métricas stop→formulario, p50/p95 y decisión de umbrales. 
