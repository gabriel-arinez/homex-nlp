# Motor determinístico definitivo de HOMEX

**Selección:** homex-nlp 0.1.18, reglas `prf04-rules-final`, RULES_ONLY.
Es una consolidación estable de V15/V16; no inicia otra campaña experimental.
La referencia de cierre será `nlp-final-0.1.18-20261029`. Su commit y el SHA256
reproducible del wheel identifican el componente. Metadatos: `nlp-final-release.json`.
Python 3.11; dependencias exactas en uv.lock. Contrato público **1.0**, sin cambios.

## Responsabilidades y autoridad

El extractor recibe texto Unicode original y moneda contextual BOB/USD. Devuelve
cero o una propuesta de MUEBLE_MEDIDA, candidatos con offsets Python [inicio, fin),
relaciones representables, advertencias y pendientes. No guarda proformas, modifica
catálogos, altera permisos ni convierte monedas. PRF-03 sigue siendo el único
configurador técnico; el vendedor revisa y confirma. Una propuesta parcial conserva
los campos independientes que tienen evidencia suficiente.

Los estados son REQUIRES_REVIEW, NO_PROPOSAL y ERROR conforme al contrato.
REQUIRES_REVIEW nunca equivale a autorización para fabricar. Los JSON Schema
congelados de `schemas/` definen entrada, salida, campos, advertencias y restricciones.
Las evidencias aceptadas, rechazadas y pendientes conservan sus spans originales.
Los IDs de componente y las referencias se validan; no hay relaciones padre-hijo
inventadas. Los modos experimentales del esquema histórico no se habilitan en runtime.

## Reglas y límites

- Se reconocen nombres del vocabulario aprobado y calificadores controlados.
  Menciones secundarias de silla/piso no excluyen automáticamente un mueble.
  Productos comerciales independientes múltiples exigen revisión sin mezclar líneas.
- Cantidad comercial, capacidad y cantidades internas son distintas. No hay
  multiplicaciones de piezas por muebles. Correcciones comerciales contiguas y
  encadenadas aplican únicamente al campo inequívoco; valores inválidos quedan pendientes.
- Dimensiones requieren eje y unidad explícitos o la enumeración final autorizada.
  Hay conversión exacta m/cm/mm; no se inventa cm para una cifra aislada ni se
  reconstruye 1.20 a partir de 0.20. Espesores de piezas tienen ámbitos locales.
- La nueva extracción oral de espesores sin pieza se conserva como evidencia
  UNRESOLVED, con resolución PRF-03; no afirma un espesor general. Los pendientes
  numéricos históricos mantienen su representación contractual y su revisión humana.
- Materiales, colores compuestos, acabados y herrajes se asocian por cláusula.
  Alternativas sin selección permanecen pendientes. Un atributo de una pieza negada
  no se propaga al mueble. «Madera clara» no afirma por sí sola material madera.
- Los precios usan Decimal. Negativos, formatos inválidos, alternativas y conflictos
  no se convierten en importes efectivos. La rectificación monetaria debe conectar
  precios; una corrección de espesor no elige otro precio.
- Unitario y total explícitos se conservan como evidencia independiente. Sin cantidad
  no se calcula su relación ni se descarta el unitario por ese motivo. Con cantidad
  conocida deben ser coherentes; un conflicto queda pendiente. El total dictado no se
  reemplaza por un cálculo. La referencia unitaria aproximada nunca es precio efectivo;
  su redondeo HALF_UP coincide con el contrato.
- El consumidor conserva los totales explícitos y ofrece resolución de espesores
  pendientes. El frontend no convierte un descuento ausente en cero confirmado;
  exige completarlo antes de confirmar. Sólo deriva un unitario cuando la cantidad,
  el descuento cero y la división exacta a centavos lo permiten. La edición manual
  y la generación vigente de captura prevalecen frente a respuestas tardías.

Vocabulario desconocido, unidades ausentes, geometrías que requieren croquis y
relaciones que el contrato no puede representar permanecen pendientes. No se
recuperan palabras inaudibles ni se corrige el ASR por conocimiento de un guion.
No hay exactitud universal del 100 % ni WER humano calculable sin referencia fiel.

## Evidencia de selección

Se reproducen V15 y V16 en sus commits exactos sobre los mismos 103 textos y
referencias congelados, conservando criterios y denominadores. El holdout ya es
conocido y no se presenta como ciego. Su regresión V16 de 19 FP/79 FN se corrige
hasta 18 FP/73 FN, frente a 18/77 en V15. Se conservan cinco guiones completos de
veinte, frente a cero de V15; el holdout integral sigue 0/5. Son referencias
asistidas conocidas, no exactitud comercial humana del audio. Los calificadores
literales penalizados por referencias abreviadas se conservan y se explican;
no se cambian las referencias para favorecer cifras.

Las nuevas regresiones prueban seguridad de precios, cantidades, ámbitos, pendientes,
negaciones y trazabilidad. Las pruebas anteriores sólo actualizan identidad de
versión y un nombre literal más completo; corpus, splits y referencias originales
no se editan. El runtime se prueba bloqueando imports NER y de investigación.

## Consumo y reproducción

```bash
uv sync --locked --extra dev
make check
make distribution-check
uv audit --locked
python3 tools/verify_nlp_freeze.py /ruta/privada/al/expediente
```

El wheel se instala desde el artefacto con SHA256 fijado; backend debe exigir
exactamente **0.1.18**, RULES_ONLY y contrato 1.0. El PR consumidor fija wheel,
lock y verificadores de worker. La integración se ejecuta en PostgreSQL/Redis
nuevos y datos ficticios. Los 20 WAV LFS y ASR congelados se verifican en el
expediente privado; no se necesitan retranscripciones por cambio NLP. La rama
operativa parte de main y no arrastra PR37, corpus nuevo, entrenamientos o pesos.
PR38 y backend43 conservan carácter histórico; no son la entrega seleccionada.

Ningún servicio operativo se actualiza. La imagen histórica con paquete0.1.0
permanece intacta. Su incorporación futura exige construir una imagen coherente
con el commit consumidor y wheel congelados; nunca instalar manualmente dentro
de un worker activo. No hay merge, migraciones históricas ni despliegue autorizados.

## Acta de cierre del desarrollo

El componente NLP queda cerrado dentro del plan actual. Quedan cerrados NER,
híbrido, entrenamiento, nuevas campañas de corpus, comparación de arquitecturas,
aprendizaje continuo y nuevas versiones experimentales del extractor. No se
requiere participación de vendedores para cerrar desarrollo. La revisión del
vendedor sigue siendo parte normal de la operación comercial.

La próxima etapa es ASR. Su optimización no modifica el motor NLP congelado:
Faster-Whisper continuará entregando texto por el contrato1.0 existente. No se
cambian aquí modelo, idioma, VAD, decodificación, caché ni infraestructura ASR.

La CI final sustituye el job histórico de entrenamiento por `rules-only-freeze`:
comprueba invariantes determinísticos y SHA256 del wheel. Los scripts de estudio
se conservan como archivos históricos, sin job de entrenamiento automático.
