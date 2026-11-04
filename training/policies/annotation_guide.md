# Anotación PRF-04

Las únicas fuentes operativas son los cuatro JSONL de `data/corpus/`. El usuario
confirmó el 21-10-2026 que los 675 registros son su fuente de trabajo y que varios
son originales. `metadata.fuente_autorizada_prf04` registra esta decisión sin
reescribir la procedencia previa por registro. No equivale a audio real revisado.

Offsets Unicode Python `[start,end)` sobre texto literal inmutable; etiquetas
permitidas en `data/manifests/prf04_labels.json`. `COMPONENTE` identifica piezas;
`CANTIDAD` representa exclusivamente cantidad comercial. La cantidad interna
se conserva en la referencia semántica como `cantidad_interna`, asociada a una
pieza: `CANTIDAD_INTERNA` no pertenece a las 24 etiquetas NER del manifiesto.
El DTO de candidatos puede transportarla como evidencia auxiliar sin ampliar
el esquema de entrenamiento. Material, color, acabado y espesor no se propagan entre ámbitos.
`PRECIO_TOTAL` y `PRECIO_UNITARIO` conservan significados distintos.

Las referencias de `data/expected/` tienen ID y hash de fuente. Se generan desde
anotaciones, independientemente del motor operativo, y declaran explícitamente
que requieren revisión de dominio antes de tratarlas como gold humano. No se
publican como métricas de productividad ni se usan para promover un modelo.

Las particiones existentes se conservaron por familia y se sellaron con hash.
No cambiar familias, texto o anotaciones tras observar test para ajustar un
candidato; una nueva edición de corpus requiere una versión y evaluación nueva.

`make corpus-check docbin-check` valida las cuatro fuentes. Los originales
anteriores, sus scripts exclusivos y copias se retiraron del árbol operativo;
el inventario previo conserva hashes/conteos y Git conserva contenido histórico.

## Corpus integral offline.5.1 (PR #37)

La fuente activa de entrenamiento experimental es el bundle privado de
`training.integral_v2.build`, con versión `2.0.0-offline.5.1`. Los cuatro JSONL
V1 anteriores siguen siendo la fuente histórica operativa inmutable. El constructor
`training.canonical_v2` y sus cifras offline.3/4 son históricos; no deben mezclarse
con los resultados del corpus integral. Ver [protocolo integral](../../docs/canonical_v2/INTEGRAL_OFFLINE5.md)
y [resultados](../../docs/canonical_v2/FINAL_OFFLINE5_1.md).

Cada ficha supervisada utiliza su bloque literal íntegro, certificado privado,
checklist y referencia comercial separada. `REVISION_TECNICA_ASISTIDA` identifica
la autoría del agente; `human_reviewed=false` es obligatorio. La cobertura revisada
no equivale a homologación por HOMEX ni a garantía automática de exhaustividad.
Una propuesta del detector no adquiere aprobación por su confianza o por sellarla:
la resolución debe documentar correcciones, evidencia literal y exclusiones.

En NER plano no se permiten spans anidados. El nombre comercial conserva su ámbito;
una capacidad o un número del SKU dentro del nombre no se vuelve `CANTIDAD`.
Materiales compuestos y expresiones con intervalo se conservan como unidades
léxicas cuando partirlos cambiaría su sentido. Una exclusión de ámbito no borra
la entidad literal: su disposición y el hecho semántico explican por qué no se
asigna un valor único al componente. Contexto sin etiqueta debe estar revisado,
no representar una sección que simplemente faltó anotar.

Los ejes explícitos sin unidad se anotan y conservan `unidad=null`: no se hereda
la unidad de otra dimensión. Una expresión multiextensión con eje explícito se
anota completa, sin inventar un escalar. Una sección sin ejes no se convierte en
alto/ancho/profundidad por orden. El espesor de cada pieza necesita evidencia de
ámbito, incluidos cantos, perfiles, puertas y mesones; una coincidencia numérica
parcial no acredita otra medida.

`CANTIDAD` es la cantidad vendida; cajones, puertas, tomacorrientes y capacidad
son hechos de la referencia, con padre y evidencia. Los conjuntos y sus piezas
conservan límites PRF-03 de 10/40. No fabricar identificadores de catálogo ni IDs
de base de datos. Un precio de catálogo es distinto de un unitario pactado.
Conservar total, descuento, moneda y reglas de derivación exacta; no inferir una
cantidad porque unitario y total coincidan. BOB por defecto es una regla del
contrato, no una prueba de moneda escrita en una proforma inexistente.

La capa oral contiene texto nuevo redactado, no audio ni transcripción humana.
Cada ejemplo declara padre(s), hash, transformación y evidencia sobre el texto
oral. Si cambia una condición comercial, se marca sintética; un subconjunto no
se anuncia como paráfrasis completa. Rectificaciones y negaciones conservan la
secuencia y las entidades canceladas sin convertirlas en valores vigentes.

### Incorporar nuevas fuentes

Custodiar el original fuera de Git con permisos privados, hash e inventario de
bloques con offsets Unicode/bytes/líneas. No inventar proforma si no está identificada.
Crear propuesta, adjudicación integral y evidencia por path; excluir individualmente
los conflictos irresolubles. Congelar certificados independientes, referencias orales
y el registro de transformaciones. Para una fuente adicional se debe ampliar el
inventario aceptado del constructor y sus pruebas con fixtures inventadas, sin
publicar el documento. No modificar una versión ya entrenada.

Construir una versión nueva dos veces con las seis entradas privadas descritas
en el runner, comprobar hashes, DocBin, relaciones, cobertura, grupos y mutaciones.
Agrupar padres, paráfrasis y plantillas antes de entrenar; no dividir un grupo
para mejorar cobertura ni modificar splits tras observar predicciones. Congelar
protocolo y código, seleccionar todos los checkpoints con dev y después evaluar.
Un holdout de documentos conocidos no se etiqueta externo o ciego. La promoción
requiere un gate distinto; este procedimiento no instala modelos en producción.
