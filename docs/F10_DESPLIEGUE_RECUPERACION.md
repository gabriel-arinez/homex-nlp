# NLP F10 — Despliegue reproducible y recuperación

## Estado

**IMPLEMENTACIÓN DEL COMPONENTE COMPLETA; CIERRE PRODUCTIVO CONDICIONADO A D07.**

F10 valida que `homex-nlp 0.1.0` puede reconstruirse, instalarse y operar dentro de la release
HOMEX sin cambiar contrato v1, `RULES_ONLY` ni la autoridad HITL. No incorpora persistencia,
colas, backups ni lógica comercial.

Referencias verificadas:

- base NLP: `8d1750b2d1d26f6d90da10603216b7926bdaf820`;
- backend F10 fusionado: `bc375894036d30cefbc8cdf7c512315aaf1ab971`;
- deploy D05/D06: `fb9c321324cfc621ac07cc42fdeb1e3257a968ab`;
- wheel consumido por backend: `homex_nlp-0.1.0-py3-none-any.whl`;
- SHA-256 del wheel: `cfacc3a987f6158f43934cb64304fa50ea3e577cfa576f3db1e6d2a9576d19e6`.

La evidencia estructurada vive en `deployment-f10-v0.1.0.json`.

## Distribución reproducible

`make distribution-check` fija `SOURCE_DATE_EPOCH=0` y ahora comprueba:

1. wheel y sdist existen para la versión declarada;
2. cada artefacto se instala en un entorno Python 3.11.15 independiente;
3. el consumidor instalado produce contrato `1.0`, modo `RULES_ONLY` y conserva el total negociado;
4. el import base no carga `faster_whisper`;
5. la metadata conserva el extra ASR `faster-whisper==1.2.1`;
6. wheel y sdist no contienen audio, `.env`, secretos ni pesos de modelos;
7. una reconstrucción limpia con la misma época produce exactamente los mismos SHA-256.

El lock sigue siendo la autoridad de dependencias para desarrollo/CI. El wheel vendorizado por
backend tiene un hash distinto al build actual porque es el artefacto histórico efectivamente
fijado; `tools/verify_backend_f10.py` demuestra que sus 21 módulos Python son byte a byte iguales a
la fuente del paquete y que backend fija paquete, ASR, wheel y hash en `pyproject.toml`/`uv.lock`.

## ASR y modelo local

El import `homex_nlp.asr` no importa `faster_whisper`, no inicializa modelos y no accede a red.
`FasterWhisperAdapter` exige primero un directorio local y entrega esa ruta a `WhisperModel`; nunca
acepta en este flujo un identificador remoto. Un modelo ausente produce `MODEL_UNAVAILABLE` antes de
importar la dependencia opcional.

`AsrService` consume todos los segmentos y elimina el archivo recibido tanto en éxito como en error.
Los errores inesperados se convierten en `TRANSCRIPTION_FAILED`, mensaje genérico y reintentable,
sin copiar la excepción, transcripción o ruta al contrato. El paquete no administra TTL, reintentos
de tarea ni huérfanos: backend/deploy mantienen esas responsabilidades y D05/D06 prueban su
recuperación y limpieza independiente.

## Concurrencia, resiliencia e idempotencia

La suite F10 ejecuta dos transcripciones simultáneas con archivos independientes y confirma ambos
resultados y cero temporales. También ejecuta 100 extracciones con dos threads sobre una instancia
de `RulesEngine`; al excluir `request_id` y latencia observacional, todas las propuestas son
idénticas y permanecen en `RULES_ONLY`.

El componente es una función de propuesta. Repetir la misma entrada conserva semántica, pero la
idempotencia de captura, intentos, outbox y redelivery pertenece a Django/PostgreSQL/Celery. Backend
F10 mantiene esas pruebas; este repositorio no simula ni duplica esas capas.

## Perfil de recursos

`tools/profile_f10_runtime.py` genera JSON agregado sin texto, audio ni paths. Mide con reloj
monotónico y CPU de proceso:

- inicialización de `RulesEngine`;
- lote de extracción concurrente;
- mediana/máximo de extracción;
- dos transcripciones simultáneas mediante doble controlado;
- RSS máximo antes/después;
- archivos de audio restantes.

El perfil CI prueba regresiones de instrumentación y privacidad; **no representa faster-whisper ni
capacidad productiva**. D07 debe medir en el equipo objetivo, con modelo local fijado, como mínimo:

- RSS del worker antes/después de cargar modelo;
- CPU, tiempo de carga y primera transcripción;
- latencia posterior y audio real autorizado;
- comportamiento de dos solicitudes en la cola con concurrencia ASR efectiva 1;
- ausencia de descarga y cero audio al terminar.

No se define un SLA con el doble ni se conserva audio para repetir la medición.

## Privacidad

Los artefactos, perfiles y logs de prueba no incluyen bytes/rutas/transcripciones. Las pruebas
provocan un error que contiene un supuesto secreto y path en la excepción interna, y comprueban que
el `ErrorDetail` público y los logs del paquete no los contienen. Los temporales se crean bajo el
directorio de pytest o `TemporaryDirectory` y deben desaparecer antes de finalizar.

D05 respalda PostgreSQL y media persistente sin audio. D06 prueba fallos y cleanup. `homex-nlp`
continúa sin almacenamiento histórico, endpoints, media comercial ni acceso a backups.

## Integración con backend F10

El gate lee el commit fusionado, no una rama flotante, y verifica:

- `homex-nlp==0.1.0`;
- `faster-whisper==1.2.1` en el worker;
- wheel y SHA-256 fijados por `uv.lock`;
- fuente pública idéntica al wheel consumido;
- adaptador backend con `MODO_OPERATIVO = "RULES_ONLY"`;
- evidencia backend de D07 pendiente, audio temporal y recuperación outbox.

No cambia `contract-v1`, schemas, endpoints, estados ni comparación HITL.

## Comandos

```bash
make check
make distribution-check
make f10-check
```

CI ejecuta los tres gates, hace checkout del backend por SHA y publica únicamente el perfil agregado
como artefacto temporal.

## Dependencia de cierre

La implementación del paquete puede fusionarse con CI verde. F10 no queda promovida a producción
hasta que D07:

- inmovilice la combinación final backend/frontend/NLP/modelo;
- ejecute el perfil de modelo real en el hardware objetivo;
- valide worker, acceso privado, temporales y ausencia de descargas;
- pruebe backup/restore y rollback según deploy;
- registre resultados y responsables operacionales.

La copia externa cifrada todavía pendiente es una condición operacional de deploy. No se adelanta
D07 ni F11 desde este repositorio.

## Evidencia local previa al PR

| Gate | Resultado |
| --- | --- |
| `make check` | 51 pruebas verdes |
| pruebas específicas F10 | 7 verdes |
| `make distribution-check` | wheel/sdist instalables y reconstrucción SHA-256 idéntica |
| contrato backend F10 | `f10-backend-contract-ok ... d07_pending=true` |
| perfil controlado | 100 extracciones, 2 workers, 2 solicitudes ASR, 0 audios restantes |

Los tiempos/RSS concretos son evidencia del host de desarrollo y no se versionan como umbral de
capacidad. CI vuelve a producir el perfil agregado por commit.

## Evidencia remota del PR

La implementación fue publicada en `feat/f10-deploy-recuperacion` con el commit
`4b5cd7432b34377468550bc5878ec50ee8cf472a` y abierta como PR
[#7](https://github.com/gabriel-arinez/homex-nlp/pull/7).

GitHub Actions [run 37960485701](https://github.com/gabriel-arinez/homex-nlp/actions/runs/37960485701)
terminó correctamente. Su job `package` validó en el mismo commit:

- entorno instalado desde dependencias fijadas;
- 51 pruebas de calidad, schemas, corpus y contratos;
- 7 pruebas específicas de F10;
- wheel y sdist instalables y reproducibles;
- compatibilidad exacta con Backend F10;
- runtime, concurrencia, privacidad y perfil agregado F10;
- publicación de artefactos de distribución y del perfil sin datos sensibles.

La evidencia remota permite integrar la implementación del componente. La promoción productiva de
F10 continúa condicionada a las comprobaciones reales de modelo y hardware definidas para D07.

## Revisión de seguridad previa al merge

El gate de distribución rechaza variantes privadas de `.env`, como `.env.production`, `.env.local` y copias de respaldo, con pruebas de regresión. `.env.example` sigue permitido por ser documentación de configuración sin credenciales. Se prueba que la serialización de `ErrorDetail` de ASR no expone rutas ni secretos.

**Límite de logging:** la excepción Python conserva `__cause__` para diagnóstico interno; un logger que emita tracebacks (`exc_info`) puede revelar la excepción original. Los consumidores backend/deploy deben impedir que esos detalles lleguen a respuestas HTTP o logs de acceso general. D07 debe verificar explícitamente esta frontera en el runtime productivo. No se modifica `src/homex_nlp` ni el wheel fijado por backend.
