# Ejemplos de integración v1

Cada archivo de `requests/` tiene el resultado normativo de igual nombre en
`expected/`. Son fixtures contractuales, no salidas de un extractor implementado.
F01 garantiza que validan los modelos y JSON Schema; F03 implementará el
comportamiento que los produce.

- `total-negociado`: cantidad 3, total exacto 100 BOB y unitario referencial.
- `precio-unitario`: 3 × 100 BOB produce 300 BOB.
- `medidas-componentes`: unidades originales, milímetros canónicos y componentes.
- `sin-producto`: propuesta nula, no un mueble vacío.
- `entrada-vacia`: texto vacío aceptado como entrada y propuesta nula explícita.
- `catalogo-fuera-alcance`: la voz v1 no crea productos maestros.
- `conflicto-multiproducto`: una captura no incorpora dos líneas silenciosamente.

Los offsets son índices Unicode de Python `[start, end)`. El consumidor web
convierte a UTF-16 solamente para presentar resaltados. La moneda procede de la
proforma. El backend debe rechazar una moneda dictada que contradiga ese contexto;
el paquete nunca convierte BOB/USD.
