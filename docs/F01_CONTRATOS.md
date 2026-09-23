# F01 — Contratos, ejemplos y políticas técnicas

**Estado: completada localmente en `refactor`.** F01 define el lenguaje común del
paquete y sus consumidores. No implementa todavía la extracción ni afirma que los
resultados esperados sean producidos por un modelo.

## Entregables

| Entrega | Resultado |
|---|---|
| `src/homex_nlp/contracts/` | Modelos estrictos de entrada, transcripción, evidencia, propuesta singular, resultado, revisión y error. |
| `src/homex_nlp/settings.py` | Configuración inyectada, modos explícitos y rutas absolutas; sin lectura de entorno al importar. |
| `src/homex_nlp/resources/` | Etiquetas/unidades versionadas; vocabulario, patrones y perfiles marcados UNCONFIGURED. |
| `schemas/` | Cinco JSON Schema Draft 2020-12 generados de forma determinista. |
| `examples/` | Siete pares request/resultado: total negociado, unitario, medidas/componentes, entrada vacía, sin producto, catálogo y multiproducto. |
| [Contrato v1](contract-v1.md) | Semántica, offsets, precio, perfiles y compatibilidad. |
| [Configuración](configuration.md) | Variables y límites de validación de F01. |
| `tools/export_schemas.py` | Generación y comprobación sin divergencia manual. |
| `tests/contract/`, `tests/unit/` | Invariantes Pydantic, JSON Schema, fixtures, Unicode, recursos y configuración. |

## Decisiones materializadas

- Una captura produce cero o una propuesta. Un resultado multiproducto o de
  catálogo fuera del alcance v1 devuelve `NO_PROPOSAL` con causa explícita.
- `TOTAL_NEGOCIADO` conserva el total exacto. Tres muebles por 100 BOB mantienen
  100.00 y usan 33.333333 solamente como referencia aproximada.
- `PRECIO_UNITARIO` requiere cantidad para calcular total y valida la multiplicación.
- Dinero y decimales viajan como strings; cantidad es entero estricto y no acepta
  booleanos. La moneda no tiene default y debe concordar request/resultado.
- Los spans usan índices Unicode Python con final exclusivo y se contrastan con el
  texto original. Campos y componentes solo referencian evidencia existente.
- La propuesta puede ser incompleta, pero no vacía. Cantidad/nombre ausentes exigen
  advertencias; no se asigna uno, cero ni valores de perfil ficticios.
- `RULES_ONLY` y `HYBRID` son estados explícitos. HYBRID requiere ruta/hash; el
  cargador y la comprobación del archivo se implementarán en F03.
- La ausencia de perfiles HOMEX es `UNCONFIGURED` y no bloquea. JSONB V1 comercial
  sigue siendo un adaptador futuro distinto del contrato rico.
- JSON Schema garantiza forma interoperable. Las validaciones contextuales
  (slice de offsets, cálculos y referencias cruzadas) se ejecutan con los modelos
  Pydantic o una implementación equivalente en el consumidor.

## Verificación

`make check` ejecuta lint, formato, `tools/export_schemas.py --check` y 24 pruebas.
Los siete requests/resultados validan tanto Pydantic como JSON Schema Draft 2020-12.
Se comprobaron además total negociado, multiplicación unitaria, valores estrictos,
propuesta nula, offsets inválidos/emoji, transcripción exacta, configuración y
precisión nula sin denominador.

El wheel/sdist se construyen nuevamente; el sdist incluye contratos, pruebas,
schemas y ejemplos, pero excluye el prototipo, SQLite y datasets. El wheel se instala sin dependencias en
un entorno aislado para CONTRACT-02. La importación raíz sigue sin cargar Pydantic,
spaCy, ASR, base de datos o red; importar `homex_nlp.contracts` sí carga Pydantic de
forma intencional. No se descargó ningún modelo ni se ejecutó entrenamiento.

## Límite y siguiente fase

F03 deberá implementar el extractor que produzca los fixtures; F01 únicamente
demuestra que esos resultados pueden expresarse y validarse sin pérdida. La
comparación HITL tiene contrato de salida, pero su algoritmo corresponde a fases
posteriores. F02 es el siguiente paso: preservar, validar y curar técnicamente ambos
corpus, fijar ontología y particiones sin fuga.
