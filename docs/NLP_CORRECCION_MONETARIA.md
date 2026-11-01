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

La comparación diferencial conserva todo el léxico cardinal aceptado previamente,
incluidas centenas femeninas y veintiuna. El candidato intermedio omitía nueve
formas; se detectaron con pruebas rojas sintéticas y se restauraron antes del
cierre. Metadatos distinguen SHA intermedio y final;0.1.18 permanece intacto.

## CORR-PLN-03 (2026-11-01)

El patrón anterior podía truncar «10 mil 500» a 10000, o a 500 en la
ruta «cada uno». Ahora consume la frase numérica adyacente completa, sin límite
de nueve tokens; valida la gramática antes de aceptar un valor. Admite
coeficiente oral o entero y resto entero de 0 a 999 o cardinal. Restos negativos,
escalas repetidas, fracciones de resto y secuencias malformadas quedan sin resolver.
No modifica texto, offsets, dimensiones ni la distinción total/unitario.

Se mantiene 0.1.19 porque es una propuesta sin tag ni release publicados
(comprobados mediante GitHub el 2026-11-01). Cada candidato anterior conserva
su commit y artefacto histórico; no se sustituye un release inmutable. La nueva
huella es `prf04-rules-money-2`. El SHA anterior ac33987d corresponde al cierre
1b35e4c, y ac19d9f9 al candidato previo al restablecimiento del léxico femenino;
ninguno prueba este cambio. El manifiesto nlp-money-release.json fija el nuevo
wheel y conserva ambos SHA anteriores como procedencia.
