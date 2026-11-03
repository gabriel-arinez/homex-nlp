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
