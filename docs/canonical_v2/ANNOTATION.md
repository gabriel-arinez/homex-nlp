# Guía documental y oral V2

Offsets Python Unicode `[start,end)` sobre texto literal; tokenización `spacy.blank("es")`.
Se conservan las 24 etiquetas de `data/manifests/prf04_labels.json`. No se añade
CANTIDAD_INTERNA al NER: sus relaciones viven separadamente en expected/research_relations.

Un extracto documental es una cadena contigua del original, con hash del documento,
ID del bloque, líneas, rango absoluto e intervalo dentro del bloque. No se concatenan
pedazos como si fueran una cita. Cada ámbito cerrado tiene todas las entidades
previstas por su regla: título PRODUCTO; cantidad/unidad comercial; precio explícito;
material/espesor local con COMPONENTE solamente cuando el nombre es literal;
clase AC; atributos de catálogo. La unidad de un espesor va dentro de ESPESOR.
Un código de catálogo puede formar parte del nombre comercial. APOYABRAZOS,
CABECERA y SOPORTE_LUMBAR abarcan la expresión del atributo, sin spans anidados.

Los precios de catálogo conservan su contexto y no rellenan un precio negociado.
Se mantiene cantidad decimal en pisos. Capacidad/patas/ruedas no se etiquetan como
cantidad comercial. Los importes contradictorios y unidades sospechosas bloquean
el ítem completo antes de extraer fragmentos; no se reparan por intuición.
Ejemplo de corrección de detector: `0,80mts` no es el error literal `80mts`.

Las relaciones de mesón y patas conservan ámbitos distintos. Un fragmento
`Mesón de melamina de 25mm` documenta solo ese componente. Un fragmento de
material sin nombre de pieza no inventa el padre: queda como hecho del fragmento.
El caso sintético conservado de tablero 18 mm / mesón 27 mm mantiene ambas piezas.
Las referencias parciales no constituyen una ficha PRF-03 completa ni una línea
comercial que pueda guardarse.

Los casos orales tienen origen SINTETICO_ORAL; no son grabaciones ni transcripciones.
Sus bases/paráfrasis conservan el grupo RC2. Los fenómenos se declaran por caso.
Negaciones/valores rectificados se conservan como OBSERVACION cuando la receta
histórica así los distingue; el valor final usa su etiqueta. Repetición de nombre
no crea segundo producto. El grupo multiproducto conserva las dos menciones y
espera abstención comercial. Anáforas ambiguas no se resuelven con invención.

Se corrigió en V2-REC-A33 la omisión de la segunda mención literal de melamina;
la relación explícita preexistente del expected se mantiene. La anotación se
corrigió por lectura del caso, no por predicciones del modelo. Los test históricos
no se curan ni originan variantes. Las referencias son técnicas, con
`human_reviewed=false`; no se atribuye un revisor humano ni una revisión comercial.

La publicación contiene casos sintéticos previamente disponibles y herramientas.
Los originales, precios reales, referencias privadas, predicciones y pesos se
mantienen fuera de Git, con manifest SHA-256 y permisos privados.
