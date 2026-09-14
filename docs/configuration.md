# Configuración del paquete

`RuntimeSettings` es estricto e inyectable. La biblioteca no lee `.env` ni
`os.environ` al importar. El punto de composición futuro decide cuándo llamar
`RuntimeSettings.from_environment(mapping)`.

| Variable | Regla |
|---|---|
| `HOMEX_NLP_MODE` | Obligatoria: `RULES_ONLY` o `HYBRID`. |
| `HOMEX_NER_MODEL_PATH` | Ruta absoluta; obligatoria solo en HYBRID. |
| `HOMEX_NER_MODEL_SHA256` | SHA-256 minúsculo de 64 caracteres; obligatorio en HYBRID. |
| `HOMEX_DOMAIN_PROFILE_VERSION` | Opcional hasta recibir perfiles reales. |
| `HOMEX_ASR_MODEL_PATH` | Ruta absoluta opcional; F05 definirá carga. |
| `HOMEX_ASR_DEVICE` | `cpu` inicial o `cuda`; default cpu. |
| `HOMEX_ASR_COMPUTE_TYPE` | int8/float32; float16 solo con cuda. |
| `HOMEX_ASR_CPU_THREADS` | Entero decimal 1–64; default 2. |

Las rutas no dependen del directorio de trabajo. F01 valida forma y coherencia,
pero no comprueba existencia/hash ni carga modelos: eso pertenece al cargador de
F03/F05. Un modo inválido falla al iniciar el consumidor; no cae silenciosamente a
RULES_ONLY.

Los recursos incluidos (`labels.json`, `units.json`, `vocabulary.json`,
`patterns.json`, `furniture_profiles.json`) llevan versión propia. Solo el cargador
de perfiles existe en F01; vocabulario y patrones permanecen UNCONFIGURED hasta su
implementación y revisión. Modificarlos exige actualizar versión y regresiones.

Los mensajes de error externos usan códigos estables y texto seguro. No deben
contener rutas, credenciales, traceback, texto completo del cliente ni `str()` de
una excepción de terceros. La API Django mapeará código, estado HTTP y
correlation_id; este último no forma parte del motor puro.
