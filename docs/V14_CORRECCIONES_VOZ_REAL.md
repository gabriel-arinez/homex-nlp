# v14: correcciones derivadas de voz real

Base: PR #30, `0f3ae5b3c406ad037bcb5b0e26de3f5aa2f0a7fe`.
Paquete corregido: 0.1.14; reglas v14; contrato 1.0.

## Causas y decisiones

En `RulesEngine.extract`, la herencia de unidad eliminaba los spans de las
medidas y aceptaba cualquier residuo formado por espacios/comas/«y».
En «120 de ancho y 75 centímetros de alto» el residuo es « y »:
se copiaba indebidamente cm del alto al ancho y se eliminaba MISSING_UNIT.
Ahora sólo se comparte la unidad situada después del último eje, fuera del
valor: «45 ancho, 45 profundo, 60 alto centímetros». Una unidad entre cifra
y eje, o ligada al último valor con eje prefijo, no autoriza esa copia.
El ancho conserva 120 sin unit/value_mm; el alto conserva 75 cm / 750 mm.

En `completar_relaciones`, el ámbito del último componente terminaba al final
del texto, salvo puntuación o campos reconocidos. «etapa» no era componente;
por ello los 18 mm caían en el ámbito de cajones. Una nueva entidad
coordinada («y/con» + cantidad) ahora corta el ámbito aunque su sustantivo
sea desconocido. Otra medida («18 mm y 25 mm») no es una nueva entidad:
ambos espesores mantienen su pieza para conservar el conflicto seguro.
No hay alias etapa→tapa: se conservan cajones/cantidad 2 y
18 mm sin component_ref. El espesor sin pieza genera revisión; backend ya
lo representa con ESPESOR_SIN_COMPONENTE y selección humana explícita.

## Evidencia local

- `make check`: 392 pruebas, Ruff y formato, esquemas, corpus y contratos OK.
- `make distribution-check`: wheel/sdist reproducibles y consumidor Django OK.
- `make f10-check`: 14 pruebas de runtime, contrato histórico F10 OK.
- Verificador backend PRF04 histórico en 8f6fed3: OK.
- `uv audit --locked`: sin vulnerabilidades conocidas.
- Wheel SHA256: `cdcdbb5c64fa7a0df0ac04495871a365f7a7c2c114b138e7c8ca62a694ecc8f3`.

Las frases nuevas son regresiones textuales y controles sintéticos; no son
una nueva evaluación ASR ni métricas de las cinco capturas. Se conservan los
controles anteriores de 120/60/75 cm, melamine/melamina y conflictos seguros.
No se modifican audios, corpus, laboratorios, capturas ni esquemas públicos.
