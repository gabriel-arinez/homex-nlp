# Incidencias y decisiones de normalización

**Regla:** corregir ortografía, puntuación y unidades inequívocas para la lectura; no inventar medidas, colores, cantidades, modelos, precios ni asignaciones. Las dudas quedan en el registro y el valor cuestionado se omite del dictado cuando corresponda.

## Inconsistencias detectadas

### MP-0003 — JUEGO DE MESAS AREA COMUN - SALA ESPERA (PROFORMAS(4).txt, bloques 3)
- FUENTE_AMBIGUA: altura de la mesa grande «40m»; se omite, no se convierte silenciosamente a 40 cm.
- FUENTE_AMBIGUA: diámetro de varillas «0.05mm» físicamente improbable; se omite.
- FUENTE_AMBIGUA: texto enumera conjuntos «1 juegos (tamaño 1 y 2), 2 juegos (tamaño 3 y 4)» sin definir los otros tamaños; solo se conserva el juego de 2 mesas explícitas.

### MP-0005 — SILLONES SALA DE ESPERA MODULAR (PROFORMAS(4).txt, bloques 5)
- FUENTE_AMBIGUA: varillas «Ø=0.05mm» improbables; se dicta material sin ese diámetro.

### MP-0009 — MESA DE REUNION PARA 10 PERSONAS (PROFORMAS(4).txt, bloques 9)
- FUENTE_INCOMPLETA: cantidad comercial no expresada de manera explícita; no se infiere a partir del total.

### MP-0012 — ATRIL (PROFORMAS(4).txt, bloques 12)
- FUENTE_AMBIGUA: «Meson 0.50 Cm» no es una medida clara (0,50 cm vs 0,50 m); se omite esa medida.

### MP-0015 — ESCRITORIO EJECUTIVO (PROFORMAS(4).txt, bloques 15)
- FUENTE_AMBIGUA: «80mts de alto» probablemente es un error de unidad; se omite altura.

### MP-0026 — ESCRITORIO EN "L" CON CAJONERA RODANTE (PROFORMAS(4).txt, bloques 26)
- FUENTE_AMBIGUA: profundidad de mesada «60,50» sin unidad o separación interpretable; se omite esa medida.
- FUENTE_CON_ALTERNATIVAS: mecanismo de cerradura ofrece opciones; se conserva «cerradura de seguridad» sin seleccionar mecanismo.

### MP-0033 — ATRIL (PROFORMAS(4).txt, bloques 33)
- FUENTE_AMBIGUA: «Meson 0.50 Cm» no permite fijar medida confiable; se omite.

### MP-0042 — ESPALDAR (PROFORMAS(4).txt, bloques 42)
- FUENTE_AMBIGUA: profundidad escrita «0,3.6 mts» no es un decimal válido; se omite.

### MP-0056 — ESCRITORIO RECTO (PROFORMAS(4).txt, bloques 56)
- VALOR_NO_CONFIRMADO: «Solamen» se conserva literalmente como color escrito; verificar si existe en catálogo.

### MP-0061 — JUEGO DE MESAS AREA COMUN - SALA ESPERA (PROFORMAS(4).txt, bloques 61)
- FUENTE_AMBIGUA: altura mesa grande «40m» y varillas «0.05mm»; omitidas.

### MP-0066 — JUEGO DE MESAS AREA COMUN - SALA ESPERA (PROFORMAS(4).txt, bloques 66)
- FUENTE_AMBIGUA: altura mesa grande «40m» y varillas «0.05mm»; omitidas.

### MP-0068 — SILLONES SALA DE ESPERA MODULAR (PROFORMAS(4).txt, bloques 68,69)
- BLOQUE_FRAGMENTADO: bloques 68 y 69 corresponden a un único renglón; se unen para un audio.
- FUENTE_AMBIGUA: varillas «0.05mm» improbables; se omite diámetro.

### MP-0074 — ESTANTE LIBRERO (PROFORMAS(4).txt, bloques 75)
- FUENTE_INCOMPLETA: falta cantidad numérica explícita; no inferirla del total.

### MP-0075 — GAVETERO (PROFORMAS(4).txt, bloques 76)
- FUENTE_CONTRADICTORIA: precio unitario Bs 1800 y total Bs 1700 sin cantidad explícita; se omite precio del guion.
- FUENTE_INCOMPLETA: cantidad comercial no expresada.

### MP-0078 — ESTANTE DE 5 ESPACIOS (PROFORMAS(4).txt, bloques 79)
- FUENTE_INCOMPLETA: cantidad numérica no expresada; no inferir.

### MP-0079 — ESTANTE DE 5 ESPACIOS (PROFORMAS(4).txt, bloques 80)
- FUENTE_INCOMPLETA: cantidad numérica no expresada; no inferir.

### SIL-0002 — SILLAS ESTATICAS (SILLAS-PISOS-OTROS(3).txt, bloques 4)
- FUENTE_INCOMPLETA: cantidad no escrita, pese a haber total comercial; no se dicta inventario.

### PIS-0002 — Piso flotante HDF NA9118 (sin marca explícita) (SILLAS-PISOS-OTROS(3).txt, bloques 5)
- FUENTE_INCOMPLETA: extracto sin encabezado Ganesha; no se atribuye marca a partir de filas similares.

### SIL-0007 — SILLA SEMI EJECUTIVA B15b (SILLAS-PISOS-OTROS(3).txt, bloques 14)
- DIFERENCIA_ENTRE_FUENTES: B15b Bs 1750 en proforma frente a Bs 1500 en inventario; ambas se conservan.

### PIS-0007 — PISO FLOTANTE "GANESHA" (SILLAS-PISOS-OTROS(3).txt, bloques 17)
- FUENTE_INCOMPLETA: frase «rayos» cortada; no se agrega UV por inferencia.

### SIL-0009 — SILLA EJECUTIVA D43 (SILLAS-PISOS-OTROS(3).txt, bloques 19)
- DIFERENCIA_ENTRE_FUENTES: D43 Bs 1200 en proforma frente a Bs 1090 en inventario; ambas se conservan.

### SIL-0010 — SILLON SEMI EJECUTIVO (SILLAS-PISOS-OTROS(3).txt, bloques 20)
- DIFERENCIA_ENTRE_FUENTES: NF-810 Bs 1500 en proforma frente a Bs 1400 en inventario; ambas se conservan.

### SIL-0011 — SILLA ESTATICA (SILLAS-PISOS-OTROS(3).txt, bloques 21)
- FUENTE_CON_ALTERNATIVAS: varios colores posibles; no seleccionar uno para el producto sin confirmación.

### SIL-0014 — SILLA COD: B15b (inventario de sillas(1).txt, bloques 2)
- DIFERENCIA_ENTRE_FUENTES: B15b en inventario Bs 1500 frente a proforma Bs 1750; no consolidar automáticamente.

### SIL-0015 — SILLA COD: B15b CELESTE (inventario de sillas(1).txt, bloques 3)
- FUENTE_CONTRADICTORIA: encabezado «CELESTE» pero descripción color «turquesa»; se preserva ambos sin asumir equivalencia.

### SIL-0016 — SILLA COD : D43 (inventario de sillas(1).txt, bloques 4)
- DIFERENCIA_ENTRE_FUENTES: D43 en inventario Bs 1090 frente a proforma Bs 1200.

### SIL-0020 — EJECUTIVA COD : NF-810 (inventario de sillas(1).txt, bloques 8)
- DIFERENCIA_ENTRE_FUENTES: NF-810 en inventario Bs 1400 frente a proforma Bs 1500.

### SIL-0023 — SILLAS DE ESPERA (inventario de sillas(1).txt, bloques 11)
- FUENTE_CON_ALTERNATIVAS: cuatro colores disponibles, no variante individual.

### SIL-0024 — SILLA OPERATIVA NF-395 (inventario de sillas(1).txt, bloques 12)
- FUENTE_CON_ALTERNATIVAS: negro, guindo y plomo.

### SIL-0029 — SILLÓN GERENCIAL NF-7782 (inventario de sillas(1).txt, bloques 17)
- FUENTE_CON_ALTERNATIVAS: texto «negro y café» puede indicar variantes o combinación; no fijar color combinado automáticamente.

## Reglas técnicas para análisis

- Los importes de proformas y de inventario representan fuentes distintas; no se toma el precio más reciente ni se fuerza equivalencia.
- En catálogo no se dicta cantidad comercial ni stock ni total de línea: la extracción de catálogo no los aplica.
- En muebles a pedido se dicta una línea comercial por audio, incluidos sus componentes; precio y cantidad solo cuando la fuente permite sostenerlos.
- Los códigos de modelos se dictan como lectura humana explícita y su reconstrucción exacta se comprueba en la transcripción real; no se presupone que Whisper los devuelva idénticos.
- Repetidos y variantes se mantienen con IDs diferentes; no son muestras independientes para evaluación final y han de quedar en la misma partición si son muy similares.
- Cada guion es referencia de lectura **antes de grabar**; una transcripción literal de referencia se acepta solo después de verificar el audio.
