# HOMEX — Corpus de grabaciones comerciales

**Estado:** guiones preparados a partir de documentos originales, sin grabaciones ASR medidas y sin cambios en código.

## Cobertura real
- `PROFORMAS(4).txt`: 80 bloques tipográficos, **79 registros** porque los bloques 68-69 son una misma proforma.
- `SILLAS-PISOS-OTROS(3).txt`: 22 extractos, cubiertos individualmente.
- `inventario de sillas(1).txt`: 19 fichas de sillas, cubiertas individualmente.
- **120 guiones**, distribuidos en 79 muebles a pedido, 31 sillas, 7 pisos flotantes y 3 otros (zócalos).
- Las filas repetidas se conservan deliberadamente, pero no cuentan como evidencia independiente de generalización.

## Qué leer y cómo grabar
1. Abre `01_muebles_pedido/GUIONES_MP.md`, `02_sillas/GUIONES_SIL.md`, `03_pisos/GUIONES_PIS.md` o `04_otros/GUIONES_OTR.md`; también puedes utilizar `GUIONES_HOMEX_LECTURA.docx`.
2. Lee **solo el texto bajo DICTADO**. No pronuncies el ID, el título, las advertencias ni el nombre de archivo. No improvises correcciones ni mantengas conversaciones con el sistema.
3. Habla de manera clara, natural y uniforme. Si te equivocas, cancela el audio y vuelve a grabar desde el principio.
4. Nombra cada grabación usando el ID exacto y conserva la extensión del archivo original: `MP-0001.wav`, `MP-0001.webm` o `SIL-0001.m4a` son ejemplos válidos. Guárdala en el subdirectorio `audios` de su categoría. **No renombres un WebM a WAV sin convertirlo.**
5. Antes de ejecutar pruebas finales, revisa `control/INCONSISTENCIAS_Y_DECISIONES.md`. Los valores cuestionados no se dan por confirmados.

## Importante sobre el contrato actual
- **Muebles a pedido**: un audio representa exactamente una línea comercial, aunque incluya varios componentes integrados. Se pueden dictar cantidades y precios cuando están claros en la proforma.
- **Catálogo (sillas, pisos y otros)**: el formulario ya conoce la categoría. El motor registra sugerencias de nombre, modelo, características y precio unitario; la cantidad de compra, el total de proforma y el stock no se aplican mediante esta extracción. Por eso los guiones de catálogo no dictan cantidades comerciales ni totales.
- Los importes son referencias **históricas**, no precios activos de producción. No aplicar a catálogo real sin revisión comercial.
- Ningún guion es una transcripción exacta de audio hasta verificar la grabación. `referencias/guiones_referencia_pregrabacion.jsonl` es gold **provisional**, no verdad acústica observada.

## Archivos para Codex
- `manifiesto.csv`: IDs, origen, familia, audio sugerido (`.wav`, sustituible por extensión real) y estados.
- `referencias/guiones_referencia_pregrabacion.jsonl`: textos de referencia, uno por audio.
- `referencias/trazabilidad_fuentes.jsonl`: texto comercial original de cada registro.
- `control/incidencias.csv`: dudas y divergencias técnicas identificadas.
- `logs/VALIDACION_PREPARACION.txt`: auditoría de cobertura y estructura.
- `control/validar_audios.py`: auditoría posterior de los audios recibidos, con listado completo y opción de exigir la cobertura total.

## Fases de evaluación sin sesgo
1. Comprobar que las **120 grabaciones** existen, son legibles y corresponden a sus IDs (sin subir los originales a un repositorio público).
2. Escuchar y verificar que cada persona pronunció fielmente el texto de referencia, o corregir la referencia literal si la pronunciación difiere.
3. Procesar las grabaciones con el ASR/NLP congelado como línea base, conservando salida completa de consola y JSON por ítem.
4. Ejecutar NLP tanto sobre la transcripción humana validada como sobre el ASR. Separar WER de errores de extracción y de aplicación en la interfaz.
5. Clasificar casos problemáticos, crear regresiones y recién entonces modificar código.
6. Reservar futuros audios inéditos para validar mejoras: los 120 guiones conocidos no bastan como conjunto ciego tras ajustar reglas con ellos.

## Carpetas por categoría
- `01_muebles_pedido/`: `MP-xxxx.txt` y audios.
- `02_sillas/`: `SIL-xxxx.txt` y audios.
- `03_pisos/`: `PIS-xxxx.txt` y audios.
- `04_otros/`: `OTR-xxxx.txt` y audios.

**Privacidad:** las fuentes reales y grabaciones deben almacenarse fuera del GitHub público de HOMEX. Los cambios de repositorio no forman parte de este paquete.
