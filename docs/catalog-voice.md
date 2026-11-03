# Catálogo por voz (0.1.20)

`homex_nlp.catalog.extract_catalog(CatalogRequest(...))` es una API independiente
para borradores de creación de `SILLA`, `PISO_FLOTANTE` y `OTRO`. La categoría es
obligatoria y procede del formulario. No se ejecuta el extractor de muebles.

El consumidor proporciona `CatalogValue` con ID, concepto, código, nombre y
sinónimos autorizados de valores activos. El paquete no contiene SKUs activos ni
convierte los productos sintéticos del corpus en productos de la base de datos.

La respuesta conserva campos, evidencias (offsets Unicode sobre el texto original),
advertencias y segmentos sin reconocer. Las contradicciones se abstienen; las
rectificaciones explícitas sustituyen candidatos anteriores conservando evidencia.
Los precios unitarios usan el parser monetario existente, son sugerencias y nunca
se derivan de totales. Cantidades y stock no se aplican a productos.

Campos comunes: nombre, observaciones, unidad_stock, precio_lista. Sillas añade
marca, modelo, color_primario y especificaciones descriptivas. Pisos añade marca,
modelo, tipo, material, diseno, acabado, espesor_mm, largo_mm, ancho_mm, m2_por_caja.
OTRO no introduce perfiles de artículos ni fichas de sillas o pisos.

Ejemplos de dictado:

- «Nombre silla ergonómica. Modelo B15b. Color negro. Apoyo lumbar regulable.
  Precio unitario mil quinientos bolivianos.»
- «Nombre piso flotante. Modelo NA9118. Espesor ocho milímetros. Material HDF.
  Precio unitario ciento veinticinco bolivianos.»
- «Nombre zócalo. Descripción zócalo de alto tráfico de ochenta por quince
  milímetros. Unidad barra. Precio unitario cincuenta bolivianos.»

Las etiquetas nombre/modelo/descripción reducen ambigüedad en dictado libre.
Los valores ausentes o no activos requieren selección manual. Los códigos
alfanuméricos dependen de la calidad ASR y deben revisarse en la transcripción.

No cambia Whisper Small, CPU/int8, su caché, sus parámetros, el contrato V1 ni las
reglas congeladas de muebles. La distribución 0.1.19 se conserva en el historial;
la ampliación se publica como 0.1.20.

## Corrección 0.1.21

Los ejemplos reales de HOMEX demostraron pérdida de nombres sin etiquetas,
medidas orales mayores de diez, combinaciones de colores y códigos truncados.
La corrección conserva los tres extractores y reutiliza cardinales, decimales,
precios y negaciones existentes. Admite frases nominales iniciales y conserva su
texto descriptivo, dos colores activos unidos por «con»/«y», códigos literales y
medidas explícitas en ambas direcciones. Las alternativas y códigos hablados
ambiguos requieren revisión. Las evidencias usan offsets del texto original,
incluso con acentos Unicode descompuestos. Los materiales de respaldo y asiento
se distinguen por su contexto; el nylon del cuerpo no implica material de base.

Los parsers monetarios, reglas de muebles y parámetros/cache ASR permanecen
intactos. Las versiones publicadas 0.1.19 y 0.1.20 se conservan; la identidad del
artefacto anterior figura en `catalog-release-0.1.20.json`.
