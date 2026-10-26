# Entrega consolidada — 2.0.0-rc.1

Cinco entregas: auditoría 675/675 y fuentes; candidato documental; corpus oral sintético;
particiones/validadores/fixtures independientes; paquete y documentación reproducible.
Artefactos 00–13 localizados en esta raíz única; implementaciones únicas indicadas en el índice 08.
Datos activos V1, runtime, reglas, wheels, lock, pyproject, APIs y consumidores permanecen intactos.
Backend/frontend se consultaron solo para lectura de contratos PRF-03/04.

Candidato técnico: 727 registros incluidos, 727 expected con evidencia, cuatro familias.
375 V1 con correcciones demostrables en anotaciones/expected, 300 sin cambio semántico principal.
12 bases documentales sintéticas nuevas, 40 frases orales sintéticas. No son audios ni piloto histórico.
En el bundle: tres originales íntegros, 120 ítems inventariados, nueve anomalías y cuatro ejemplos
reales parciales, todos privados y excluidos de entrenamiento/test supervisado.

Criterios estructurales, preservación, aritmética aplicable, offsets spaCy, trazabilidad interna y
fugas conocidas de detectores se verifican automáticamente. Homologación comercial humana,
independencia humana del gold y test externo de voz siguen pendientes y no se declaran cumplidos.
Los splits conservadores dejan 38/12/677, con todos los V1 en test retrospectivo: no vender este
candidato como dataset equilibrado o prueba de mejora de campo. No se entrenó ni se promovió motor.

Privacidad: solo sintéticos previamente autorizados, recetas nuevas y hashes de originales entran
a Git. Textos reales/precios negociados, rutas personales y diagnósticos privados quedan en bundle
con permisos 700/600. El índice del bundle identifica cada sección y su condición pública/privada.
Publicación y SHA/PR efectivos se registran en evidence/publication.json del bundle; no se atribuye
un PR hasta que exista respuesta del servicio. La rama base v12 continúa separada del frente A.

Siguiente paso del plan maestro: homologación comercial de referencias y nueva fuente independiente
para ampliar entrenamiento; después experimento controlado reglas/NER/híbrido y evaluación externa
con voz humana autorizada. No activar V2 ni reinterpretar el contrato durante este encargo.
