# Guía nueva del candidato V2

La guía operativa V1 sigue intacta. Etiquetas NER exactas (24): ACABADO, ACCESORIO, ALTO, ANCHO, APOYABRAZOS, CABECERA, CANTIDAD, CLASE_RESISTENCIA, COLOR, COMPONENTE, DESCUENTO, DIAMETRO, ERGONOMIA, ESPESOR, LARGO, MATERIAL, OBSERVACION, PRECIO_TOTAL, PRECIO_UNITARIO, PRODUCTO, PROFUNDIDAD, SISTEMA, SOPORTE_LUMBAR, UNIDAD_MEDIDA.
`CANTIDAD_INTERNA` es una relación semántica; NO es una etiqueta NER permitida.
Orígenes, revisión y fenómenos son metadatos, nunca clases NER nuevas.

Offsets sobre Unicode Python sin normalización, intervalos `[start,end)`, texto literal y hash.
Spans ordenados, sin solapes; spaCy español debe aceptar `char_span(..., alignment_mode="strict")`.
Un material/espesor/color/acabado pertenece al componente delimitado por evidencia, sin propagación.
Tablero de 18 mm y mesón de 27 mm son dos afirmaciones distintas. Nombre/cantidad interna de
cajones no equivale a dos cajoneras; las relaciones conservan el objetivo correcto.
`una mesa central y dos laterales` no incrementa la cantidad comercial del juego.
`para diez personas` es capacidad, no diez mesas. Se permiten OBSERVACION para la frase contextual
y relaciones auxiliares para conteos, sin inventar NER. Sin datos no se completa cantidad.

Precio unitario, total explícito y descuento de línea se distinguen por contexto literal.
Decimal preserva centavos. Solo total inequívoco + cantidad conocida + descuento explícito cero
+ división exacta permite `derived_unit_price`. Descuento ausente se mantiene null: no autoriza
una derivación. Para V1, una ecuación total=unitario*cantidad sin descuento escrito comprueba
consistencia de importes explícitos; no afirma una declaración de descuento cero.
Moneda mencionada queda literal; moneda de Condiciones ausente no se inventa ni se convierte.
Un número sin modalidad de precio se conserva como observación y no se vuelve unitario.

`a elección`, `por confirmar`, `según diseño` expresan pendientes; no COLOR positivo.
En rectificaciones la primera afirmación reemplazada se marca OBSERVACION; la nueva conserva su
entidad y la decisión semántica explicita el reemplazo. En negaciones no se acepta el atributo negado.
En anáforas solo se resuelve un antecedente explícito único. Ante falta de antecedente queda null.
Para dos productos independientes y cancelaciones se espera ABSTAIN y ninguna propuesta fusionada.
Las dimensiones sin eje/unidad y unidades sospechosas se conservan literalmente, sin corregir 40 m
ni 80mts. La investigación no habilita voz UI para sillas/pisos/otros.

Sillas sin código verificable no reciben SKU; código ficticio de estrés se declara no confirmado.
Pisos: M2 decimal; zócalos: BARRA, distinto de largo físico 2,44 m. No convertir metros a barras.
Catálogo y cotización negociada tienen contextos distintos y fechas que pueden no constar.

Cada referencia lleva hechos con evidencia exacta, componentes/atributos y calidad de revisión.
V1: auditor literal con gramática explícita, independiente de spans/expected V1 y del runtime;
esto no es una segunda anotación humana ni independencia estadística del conjunto de prueba.
Nuevos: recetas semánticas explícitas escritas antes de renderizar NER. Tests de mutación usan
fixtures propios y comprueban cantidades, negaciones, ámbitos, precios y preservación de datos.
Las referencias tienen cobertura comercial/relacional declarada; los atributos de catálogo son
literales de investigación, no todos campos técnicos normalizados. No afirmar gold humano.

Cada registro incluido tiene referencia y procedencia; todo documento privado sin homologación
permanece en cola, incluidos cuatro ejemplos documentales parciales de las cuatro familias.
`REQUIRES_REVIEW` es una salida técnica revisable; `REQUIERE_REVISION_HUMANA` en cola documental
impide usar datos comerciales dudosos como supervisión. Los estados no se añaden a contratos API.
PRF-03 mantiene 10 conjuntos/40 componentes, atributos, accesorios y descripción original.
`schema_version=1.0` pertenece al contrato NLP; no al JSONB comercial `datos_tecnicos`.
