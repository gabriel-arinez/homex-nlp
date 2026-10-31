# CORR-PLN-01 — parche monetario 0.1.19

La regex numérica de price_mentions capturaba solo el coeficiente en una escala
mixta. El lector oral reutilizaba la gramática dimensional limitada a9999.
Se incorpora monetary.py como lector monetario acotado e independiente: Decimal,
cardinales hasta999999 y coeficiente numérico seguido de mil, solo después de
marcadores monetarios explícitos. Escalas desconocidas/inválidas no se truncan.
No sustituye texto, offsets, medidas, cantidades ni términos de negación.

Ejemplo sintético: «precio total negociado doce mil bolivianos» y «precio total
negociado 12 mil bolivianos» conservan total12000. «12 milímetros» no es importe.
La política numérica existente admite agrupadores completos conocidos, tanto punto
como coma; no se redefine regionalidad ni se acepta un formato parcial inválido.
Contexto BOB/USD sigue siendo explícito y conflictos de moneda requieren revisión.

Contrato1.0 y RULES_ONLY permanecen. Cambia huella a prf04-rules-money-1 porque
cambió semántica del parser. La versión0.1.18, su wheel y manifiesto final quedan
históricos intactos; 0.1.19 es un parche autorizado posterior, no una sustitución
silenciosa ni un nuevo entrenamiento. Metadatos: nlp-money-release.json.

Pruebas: nuevas regresiones de escalas, signos, ámbito, dimensiones, repetición,
serialización, múltiples muebles y falsos positivos, además de suite completa.
Los tests antiguos solo actualizan identidad esperada. Corpus y referencias no
se modifican. No se atribuye exactitud comercial humana a textos sintéticos.

Reproducción: uv sync --locked --extra dev; make check; make distribution-check.
Build determinístico SOURCE_DATE_EPOCH=0. Backend requiere consumidor0.1.19 con
wheel/SHA fijados en PR dependiente. Sin merge, tag final ni despliegue.
