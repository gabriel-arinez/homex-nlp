# Cobertura y calidad declarada

727 incluidos: 675 V1 + 12 bases documentales sintéticas nuevas + 40 orales sintéticos nuevos.
687 documentales sintéticos, 40 orales. Estados V1: {"APROBADO_SIN_CAMBIO": 300, "CORREGIDO": 375}.
Correcciones sin cambiar texto: descuentos explícitos en expected, relaciones de cantidad interna,
capacidad separada, y 56 spans de accesorio ampliados a incluir el núcleo «Membrana protectora».
Los 375 CORREGIDO pueden tener varias causas; no sumarlas como registros distintos.
Los 300 APROBADO_SIN_CAMBIO conservan la semántica principal; el envoltorio V2 y su evidencia son nuevos.

| Familia | Incluidos |
|---|---:|
| muebles_pedido | 414 |
| otros_productos | 103 |
| pisos_flotantes | 103 |
| sillas | 107 |

38 train / 12 dev / 677 test. Los 675 V1 se conectan por uniones transitivas de proforma,
familia, plantilla enmascarada y prefijo. Al contener test histórico, prevalece test para todo
el componente. No se entrenó sobre ese grupo. Los 52 nuevos se agrupan por caso base y familia
semántica, sin cuotas artificiales: muebles/pisos de desarrollo de datos van a train, sillas/otros
a dev y dos negativos fuera de alcance a test. No hay variantes orales de casos V1 test.
La semilla declarada 20261025 identifica el plan determinista; no hay sorteo aleatorio ni ratio objetivo.
Este test retrospectivo fue leído al auditar; no es ciego ni humano externo. Queda sellado para
entrenamiento a partir de este candidato, y no se evaluó un motor para seleccionar cambios.
Los tamaños no sostienen aún una comparación representativa entre modelos; no ocultar esta limitación.

34 señales históricas reconstruidas: falsos positivos como exigencia de etiqueta NER inexistente,
con relaciones internas explícitas confirmadas y registradas. 79 grupos de prefijos entre particiones
V1; riesgo de plantilla confirmado, no 79 copias de documentos. 39 pares con Jaccard de 4-gramas >=0.50,
todos tratados dentro de partición. El validador recalcula pares entre splits; cero riesgos conocidos
sin tratar con esos detectores. No es demostración universal de ausencia de similitud semántica.
No hay duplicados exactos. Las tablas de grupos/pares y decisiones son parte del manifiesto.

24 etiquetas presentes, 69 fenómenos declarados (ver CSV, conteos por denominador 727).
La cobertura de fenómenos no es una estimación de frecuencia de vendedores.
Tipos: {"AMBIGUO": 15, "NEGATIVO": 3, "POSITIVO_PARCIAL": 34, "POSITIVO_SINTETICO": 675}.
Vocabulario regional, perturbaciones ASR y oralidad son sintéticos explícitos.
Piloto antiguo 48 no encontrado, 0 incorporados desde ese piloto.

Trazabilidad interna: 727/727 texto→fuente/receta→NER→expected→grupo→split.
Correspondencias auténticas V1 confirmadas: 0/675; no se certifican por compartir título.
Privados: 120/120 ítems con archivo/hash/bloque/líneas/bytes; 4 ejemplos parciales con vínculo literal.
Vínculos documentales se validan en el bundle, fuera de Git. No atribuir los 727 a cotizaciones reales.
Voz humana, ASR real, anotación humana independiente y test externo humano: 0.
