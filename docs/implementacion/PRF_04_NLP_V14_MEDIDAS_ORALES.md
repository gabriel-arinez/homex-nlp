# PRF-04 — NLP v14: medidas orales compuestas y especificaciones explícitas

Base exacta: `7b7bea6f0fca8ca4e305537ef86da3010c2071f8` (#29).
Rama aislada: `codex/prf04-nlp-v14-medidas-orales`.
Paquete `0.1.13`, reglas `prf04-rules-v14`; contrato público **1.0**, modo
**RULES_ONLY**, resultado **REQUIRES_REVIEW**. No se cambian contratos/schemas,
backend, frontend, corpus ni bases de datos. No hay merge ni despliegue.

## Diagnóstico y cambio

`find_measurements` aceptaba sólo una magnitud seguida de una unidad. En el texto
proporcionado por el usuario, `un metro 20 de ancho` se truncaba a `20 de ancho`,
con unidad y valor normalizado ausentes. Las dos variantes en palabras no daban
ancho. Alto y profundidad ya resultaban correctos.

La nueva ruta dimensional reconoce metros enteros + resto centimétrico con eje
explícito, usa Decimal y el lector de números en palabras existente. Sustituye
sólo los matches simples contenidos en el span compuesto; una expresión compuesta
inválida tampoco puede convertirse en un prefijo/sufijo dimensional aceptado.
Las reglas comerciales de cantidades/precios no reciben este léxico numérico.

El contrato representa la medida compuesta en una sola unidad: **120 cm →
1200 mm**. `original_text` y el candidato conservan íntegramente «un metro 20 de
ancho» (o su variante), incluidos offsets Unicode sobre el original inalterado.
`normalized_value=["120","cm"]` permite auditar la conversión sin modificar texto.

Con la misma frase de escritorio y el mismo alto/profundidad:

| Variante de ancho | Base #29 | v14 | Alto / profundidad v14 | MISSING_UNIT v14 |
| --- | --- | --- | --- | --- |
| un metro 20 de ancho | 20, sin unidad ni mm | 1200 mm | 750 / 600 mm | No |
| un metro veinte de ancho | ausente | 1200 mm | 750 / 600 mm | No |
| un metro y veinte centímetros de ancho | ausente | 1200 mm | 750 / 600 mm | No |

`melamina` ya tenía candidato MATERIAL en la base. `melamine` no estaba en el
léxico; `blanca` tampoco (sólo `blanco`). Además, los candidatos COLOR nunca se
proyectaban a `primary_color`. Ahora se conserva evidencia MATERIAL de ambos
textos; la variante ASR se normaliza a `melamina` con aviso informativo UNKNOWN_TERM
para revisión. Se reconoce el femenino del color. Sólo una especificación directa
`producto de material color`, cerrada por puntuación/fin, sin materiales/colores
competidores ni señales de alternativa/rectificación, autoriza `primary_color`.
`blanca` se representa como `blanco`, con su evidencia literal y sin component_ref.
Material/color explícitamente negados se conservan como candidatos REJECTED.

No existe campo material en ItemProposal 1.0: el material general permanece como
candidato MATERIAL con `component_ref=null`. No se agregan propiedades, componentes
ficticios ni IDs de material/catálogo. Los componentes reales mantienen sus ámbitos;
el color de una tapa no se propaga al color principal del mueble.

## Alcance conservador y limitaciones

- Metros enteros 1..9, con concordancia metro/metros; resto explícito 1..99 cm.
- Elipsis sin `y` (`un metro veinte`, `un metro 20`): resto 10..99. Con `y` se exige
  unidad centimétrica explícita. No interpretar `un metro cinco` ni `un metro y veinte`.
- No sumar restos ≥100 ni otras combinaciones de unidades; no adivinar fracciones
  como `un metro y medio` ni decimales orales como `dos coma cinco metros`.
- Los ejes/unidades simples y enumeraciones de unidad final compartida conservan
  su comportamiento. Sin unidad inequívoca, sigue la abstención/advertencia existente.
- La asignación de color principal es intencionalmente más estrecha que el
  reconocimiento de candidatos; fuera de la asociación inequívoca permanece vacía.
- La corrección `melamine` es una interpretación contextual revisable, no una
  validación humana ni una asociación con un material del catálogo del backend.

## Reproducción y verificación

Desde este checkout, Python 3.11.15 / entorno fijado de uv.lock:

```bash
uv sync --locked --extra dev --python 3.11.15
uv run --locked --extra dev pytest -q \
  tests/unit/test_prf04_medidas_compuestas_v14.py \
  tests/unit/test_prf04_numeros_dimension_v12.py \
  tests/unit/test_prf04_semantics.py \
  tests/unit/test_prf04_piloto_comercial_02_05.py \
  tests/unit/test_prf04_piloto_dimensiones_09.py
make check
make distribution-check
uv audit --locked
git diff --check
```

`make check` incluye suite completa, Ruff check/format, schemas v1 y comprobación
sólo lectura del corpus existente. La distribución se construye reproduciblemente
y prueba wheel/sdist instalados. No se ejecuta ASR ni se requieren audios/modelos
para el reproductor o los tests de v14.

Comparación ejecutable de las tres transcripciones:

```bash
uv run --locked --extra dev python - <<'PY'
from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine

for medida in ('un metro 20', 'un metro veinte', 'un metro y veinte centímetros'):
    texto = (f'Necesito un escritorio de melamine blanca, de {medida} de ancho, '
             '60 centímetros de profundidad y 75 centímetros de alto.')
    r = RulesEngine().extract(ExtractionRequest(
        request_id='comparacion-v14', text=texto, currency_context='BOB'))
    r = ExtractionResult.model_validate_json(r.model_dump_json())
    dims = {d.axis: d.value_mm for d in r.item_proposal.dimensions}
    assert dims == {'ancho': '1200', 'alto': '750', 'profundidad': '600'}
    assert not any(w.code == 'MISSING_UNIT' for w in r.warnings)
    assert r.status == 'REQUIRES_REVIEW' and r.engine.mode == 'RULES_ONLY'
    assert r.schema_version == '1.0'
    assert all(texto[c.start:c.end] == c.text for c in r.candidates)
    print(medida, dims, r.item_proposal.primary_color.value)
PY
```

Los tests cubren las tres variantes con ambas grafías de material, ambos órdenes
de eje, ejes alternativos, rangos, gramática/unidades ambiguas, offsets Unicode,
normalización exacta, componentes y color no propagado, negación/alternativas,
precios, cantidades, espesor y round-trip del contrato. La antigua prueba negativa
de `un metro y veinte centímetros de alto` pasa al conjunto positivo de v12.
Las comprobaciones de versión se actualizan sin cambiar los invariantes públicos.

La intervención humana sigue siendo necesaria para aceptar/corregir la propuesta,
confirmar la interpretación ASR y vincular materiales/colores con el catálogo real.
El PR draft contiene SHA final, resultados y enlaces de CI para esta revisión.
