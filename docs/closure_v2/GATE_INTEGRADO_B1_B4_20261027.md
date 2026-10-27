# HOMEX — Gate integrado y plan de ejecución verificable B1–B4
**Fecha:** 2026-10-27 · **Dependencia:** NLP #31 (`fb1ad97b`), auditoría #34.  
**Naturaleza:** revisión remota y plan operacional **sin fabricar homologaciones ni métricas**. Esta entrega no activa corpus V2, modelos ni cambios en producción.

## 1. Hallazgos cruzados: no volver a generar candidatos ya existentes
| Evidencia | Estado y límite |
|---|---|
| NLP #20 / 0154ecb | RC1: 727 registros (687 sintéticos documentales, 40 sintéticos orales). 375 propuestas de corrección; 675 V1 conectados transitivamente por grafo de fuente/plantilla y test histórico. Partición retrospectiva no es holdout independiente. |
| NLP #22 / b27edfa | RC2: 66 sintéticos (39 train / 27 dev) y 46 grupos efectivos; 375 cambios de V1 + muestra estratificada para homologación. Gold externo = 0. |
| NLP #24 / 4c94a75 | Experimento controlado 16 muebles dev sintéticos / 98 entidades: F1 candidatos ACCEPTED v13=0.4521; NER=0.3824; híbrido=0.4521. Raw NER=0.6000, raw reglas=0.4837. No es evaluación externa ni comparación v14. |
| NLP #28 / 544f680 | Herramienta de doble escucha, aprobación independiente y exportación privada de referencias humanas/score WER; **no** hay referencias HUMAN_GOLD aprobadas demostradas. |
| NLP #31 / fb1ad97 | Overlay inactivo: 577 filas train/dev, 49 extensiones literal «Membrana protectora», 277 filas con hechos (247 descuento, 35 cantidad interna, 12 capacidad). |
| NLP #34 / 4692085 | Dictamen independiente, CSV de los 49 ítems sin aprobación/estado documental. |
| NLP #32 / 4dc3f25 y backend #39 / 7ac385d, frontend #42 / ba6de1b | Línea runtime v14/0.1.14 separada; no sustituir con métricas antiguas ni intervenir sobre esas ramas. |

**Alerta de mayor impacto:** #20 documenta un **grupo transitivo de 675 V1** al cruzar plantilla/familia/proforma. Aunque #31 no detecta solapamiento directo de IDs entre splits y reduce el síntoma a 79 grupos de prefijos, los resultados **no son incompatibles**: utilizan relaciones y denominadores distintos. No asumir que train/dev/test V1 sean semánticamente independientes. Las métricas perfectas NER del dev sintético de #31 no habilitan despliegue.

## B1. Pruebas reproducibles requeridas
Preparar checkout independiente de NLP #31 por SHA, sin tocar el worktree principal ni `main`. Guardar todas las salidas temporales en `~/Descargas/`. Inventariar las 12 huellas de corpus/splits/expected, verificar `git status --short`, `git diff --check`, `make closure-v2-check`, `make check`, `make docbin-check`, `make distribution-check`. Distinguir PASS local de reportes declarados por PR. Documentar vulnerabilidades preexistentes de `uv audit --locked` en lugar de omitirlas. No ejecutar tests backend contra base histórica.

Criterio de cierre B1: ejecución reproducible y contraste de cada hallazgo con hash/revisión, sin alteración de V1. Estado actual: **no cerrado**; la revisión remota no ejecuta el checkout del equipo del usuario.

## B2. Procedimiento de homologación real
- El archivo `COLA_REVISION_49_ACCESORIOS.csv` está preparado, con 49 IDs únicos, 44 train y 5 dev; todos requieren revisión. No contiene texto original ni nombres comerciales sensibles.
- Fuente real necesaria: documentos comerciales auténticos (dos TXT coincidentes por hash en #31; tercer inventario de sillas no disponible en el checkout auditado) y kit de adjudicación de RC2 #22. **SHA de TXT coincidente no demuestra enlace a cada registro sintético**.
- Relacionar cada candidata con `source_document_id`, `source_item_id`, evidencia localizable y decisión independiente; `NO_IDENTIFICADA` permanece sin vinculación, no rellenar automáticamente.
- Primera revisión: 49 límites de ACCESORIO. Segunda: 35 cantidades internas y 12 capacidades. Tercera: 247 descuentos; no sobreescribir precios, monedas ni unidades. Consultar también las 375 propuestas RC1/RC2, sin fusionarlas automáticamente con las 49.
- El test V1 de 98 filas solo lo puede custodiar quien supervise el sellado; no utilizar correcciones de test para optimizar/dev. Si hay conectividad transitoria por plantillas/fuente, diseñar evaluación nueva por fuentes independientes, en vez de barajar filas.

Decisión sobre cada anotación: `APROBAR`, `CORREGIR_CON_EVIDENCIA`, `DESCARTAR` o `PENDIENTE`, con identidad autorizada del revisor, fecha, evidencia y valor antes/después. Sin acta auténtica, conservar `PENDIENTE`. Resultado de B2 **bloqueado para homologación**, aunque las matrices técnicas existen.

## B3. Ingesta oral: piloto e independencia
- Revisar piloto de **48 frases propuestas** con material original verificado; no asumir integración ni totalidad utilizable. RC1 aporta 40 sintéticos y RC2 añade 14 casos; **no** sumarlos como nuevos independientes ni equipararlos a los 48 antes de verificar solapamientos.
- Etiquetar fenómenos por caso/grupo: cantidad comercial vs capacidad/interna; negación, rectificación, precios, medidas con y sin unidad, material y color, asociación espesor/componente, vocabulario melamina, dos productos, abstención, errores de ASR. No convertir guion en transcripción de audio.
- `training/closure_v2/oral.py` valida identidad, hashes, privacidad declarada, offsets y ausencia de cruces entre splits. **Limitación verificada de código:** el validador no mide independencia semántica; rechaza grupos idénticos por ID, pero no paráfrasis con IDs distintos. Las referencias `authorization_ref`, `privacy_review_ref` y `human_review_ref` pueden ser cadenas sin verificación externa, por lo que un PASS solo implica conformidad de estructura, no consentimiento real.
- El piloto WAV de 20 archivos se procesa en privado con el instrumento #28; la escucha doble ha de provenir de personas distintas e independientes del ASR. Sin referencias, `WER=null`.
- No copiar audios, nombres, textos privados, firmas, claves ni consentimientos a Git.

Estado B3: infraestructura y controles ya existentes, **pendiente** etiquetado/homologación y cobertura real certificada.

## B4. Evaluación comparativa correcta
**No equiparar** las métricas del diagnóstico v6/62 dev (NER+ensamblador F1 1.0) con las de rc2/v13/16 dev. El primer experimento tiene advertencia de similitud de plantillas, evaluación con referencias sintéticas y diferente versión; el segundo muestra que puntuación raw y puntuación ACCEPTED pueden ordenar motores de forma opuesta.

Gates nuevos antes de cualquier promoción:
1. Dataset de desarrollo homologado y una prueba externa independiente por plantilla, cliente/fuente, grupo, hablante y sesión. Sin compartir etiquetas del externo con quienes entrenan o seleccionan.
2. Predeclarar selección entre A reglas V14 actuales, B NER+ensamblador, C híbrido/veto; comparar versiones y SHA exactos bajo **la misma** transcripción y referencia.
3. Evaluar precisión/recall/F1 por entidad y micro/macro **y** coincidencia estructural: unidad/eje, vínculo componente–espesor, accesorios, materiales por pieza, precio total/unitario, cantidad comercial/capacidad/interna, negaciones/rectificaciones, propuesta falsa, abstención y correcciones humanas.
4. Latencia cold/warm, p50/p95, hardware y n explícito: ASR, cola/outbox, NLP, backend/proyección y render E2E. No extrapolar de milisegundos de extracción a UX.
5. Computar WER solo contra referencia humana del mismo audio con S/D/I/N, normalización publicada, permisos y revisión; si falta, devolver `null`.
6. No desplegar NER/híbrido automáticamente aunque alcance F1 alto sobre sintéticos. Requiere gate de integridad comercial, reproducciones independientes y aceptación del usuario.

Estado B4: comparadores históricos auditados; **pendiente** experimento sobre V14 y datos humanos independientes.

## Criterio de entrega a la siguiente sesión
Resultado ya publicable: diagnóstico, cola de 49, trazabilidad y protocolo de adjudicación/comparación. No existe base suficiente para declarar terminadas las homologaciones B2/B3 o una evaluación final B4. No habilitar PR #31/#34 a merge o training hasta resolución formal de los bloqueos.

## Comandos seguros para reproducir en Linux del usuario
Estos comandos **solo leen el checkout existente**, no fuerzan ramas ni descargan dependencias. No presuponen que la ruta esté efectivamente disponible; observar errores si falta:
```bash
cd "$HOME/HOMEX/homex-nlp"
printf '\n===== GIT =====\n'
git status --short --branch
git worktree list
git rev-parse HEAD
git remote -v
printf '\n===== RUTAS DE AUDITORÍA =====\n'
git ls-files 'data/corpus/*' 'data/splits/*' 'data/expected/*' 'training/closure_v2/*' 'docs/closure_v2/*'
printf '\n===== HERRAMIENTAS =====\n'
command -v uv
command -v python3
```
Para ejecutar checks de #31 de forma aislada, primero identificar worktree ya existente o crear uno nuevo **después de verificar el estado local**. Nunca ejecutar `git checkout main` si otro worktree la ocupa; no usar `reset --hard`, `clean -fd` ni `push --force`.
