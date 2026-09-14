# F00 — Preparación y protección del punto de partida

**Estado: completada localmente.** Rama `codex/f00-preparacion`.
Punto de partida: commit `9beefd065c0d76ac1896287232a2f80697ef17cb`.
No se ha ejecutado F01 ni se han modificado los flujos comerciales del prototipo.

## Protección del punto de partida

[Manifiesto previo](baseline/f00-manifest.json): SHA-256 y tamaño de los 36 archivos
existentes relevantes, incluido código, SQLite experimental, SQL v3, ambos datasets
y documentación de auditoría. `docs/` ya estaba sin seguimiento al iniciar; se
conservan sus archivos anteriores salvo la actualización autorizada del plan.
El manifiesto registra también la referencia del SQL original recuperable desde
Git y su hash; no se crea otra copia operativa de esquema.

`python3 tools/verify_baseline.py` verifica **34 archivos intactos**. Las dos
modificaciones autorizadas del conjunto original son `.gitignore` y el Plan Maestro.
El verificador no importa el prototipo ni abre SQLite como base de ejecución.
Este manifiesto acredita preservación; no sustituye commits/backups del proyecto.

## Archivos y decisiones incorporadas

| Entrega | Contenido |
|---|---|
| [Plan Maestro 2.1](PLAN_MAESTRO_REFACTORIZACION_HOMEX.md) | Respuestas finales integradas en precios, nota, recibos, idempotencia, catálogo, perfiles y pruebas; preguntas G01–G03/P29–P32 cerradas. |
| [Arquitectura](architecture.md) | Límites paquete/Django/worker/Vue y separación del prototipo. |
| [Integración Django](integration-django.md) | Persistencia, estados, transacciones y ampliaciones aprobadas pendientes de F07/F08. |
| [Matriz de requisitos](requirements.md) | Regla → fase → condición de aceptación, incluyendo T01–T09. |
| `pyproject.toml`, `uv.lock`, `.python-version` | Python 3.11.15; dependencias directas y extras separados, 66 paquetes resueltos en lock. Hatchling 1.32.0 para build. |
| `src/homex_nlp/__init__.py` | Paquete mínimo importable, sin modelo, DB, red ni lógica comercial. |
| `tests/contract/test_import.py` | CONTRACT-02 desde proceso aislado, directorio externo e importaciones de infraestructura bloqueadas. |
| `.github/workflows/ci.yml`, `Makefile` | Instalación desde lock, lint/formato/tests, build e importación del wheel aislado. |
| `README.md`, `.env.example`, `.gitignore` | Comandos actuales, alcance, ausencia de variables obligatorias en F00 y exclusión de entornos/secretos/artefactos. |

El entorno nuevo se creó en `.venv`; `backend/.venv` sigue intacto. Runtime usa
spaCy 3.8.13 y Pydantic 2.13.4 observados en el proyecto, sin copiar todas las
transitivas del requirements experimental. Los extras ASR/demo se resuelven en el
lock, pero no se instalan para las pruebas de F00. No se descargaron modelos.

## Verificación ejecutada

| Comprobación local | Resultado |
|---|---|
| `uv sync --locked --extra dev` con Python 3.11.15 | Instalación limpia en nuevo entorno; runtime/dev separados de extras ASR/demo. |
| `uv lock --offline --check` con caché preparada | Lock compatible con pyproject. |
| `make check` sin red, con caché preparada | Ruff lint y formato correctos; CONTRACT-02: **1 passed**. |
| `uv build --offline` con caché preparada | Wheel y sdist construidos; backend de build fijado. |
| Wheel instalado con `--no-deps` en otro entorno | CONTRACT-02 pasa también allí, sin spaCy/Pydantic/ASR instalados. |
| Inspección de wheel/sdist | No incluyen backend experimental, SQLite ni datasets. |
| `python3 tools/verify_baseline.py` | 34 archivos originales intactos; dos cambios autorizados delimitados. |

Los artefactos locales son `dist/homex_nlp-0.1.0-py3-none-any.whl` y
`dist/homex_nlp-0.1.0.tar.gz`, excluidos de Git. Se instalaron dependencias desde
PyPI para preparar la caché; no se afirma instalación offline sin caché. La CI está
configurada y sus operaciones equivalentes se comprobaron localmente; aún no se
ha ejecutado el workflow en GitHub.

## Límite de la entrega

El SQL v3 y datasets no cambian en F00. Los dos modos de precio, recibos
EMITIDO/ANULADO, clave_idempotencia e integridad SQL son requisitos aprobados para
sus fases respectivas. No hay entrenamiento, nuevas APIs comerciales, importación
de catálogo, migraciones Django ni despliegue. El siguiente paso del plan es F01:
contratos, ejemplos y políticas técnicas, con las decisiones ya cerradas.
