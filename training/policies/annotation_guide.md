# Guía de anotación y curación F02

La fuente comercial contiene 200 cotizaciones bajo la clave `label`. La copia
curada cambia esa clave a `entities` y conserva texto, etiquetas y orden. Cada
registro incorpora un ID estable, hash de texto y familia. Ninguna ausencia de
etiqueta significa un valor por defecto ni un negativo implícito.

Los offsets son índices Python Unicode, inicio inclusivo y fin exclusivo. Deben
seleccionar texto real y coincidir estrictamente con `spacy.blank("es")` de la
versión indicada en el manifiesto. Una corrección semántica exige revisión
comercial; F02 solo corrige los límites técnicos registrados en `changes.jsonl`.

`PRODUCTO`, `CANTIDAD`, dimensiones, `ESPESOR`, `ACCESORIO`, `OBSERVACION`,
`PRECIO_TOTAL` y `MATERIAL` se conservan para el alcance de muebles. Las etiquetas
de sillas se preservan en su corpus aislado: `MODELO`, `ERGONOMIA`,
`APOYABRAZOS`, `CABECERA`, `SOPORTE_LUMBAR`, `SISTEMA`, `INCLINACION`,
`POSICIONES`, `COLOR` y `DISENO`. Esta conservación no amplía el entrenamiento
v1 de muebles ni habilita altas automáticas de catálogo.

Las particiones se construyen por familia anotada. El test se sella al crear el
manifiesto y no se vuelve a generar durante el ajuste de reglas o hiperparámetros.
