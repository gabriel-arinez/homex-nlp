# Ingesta oral V2 y privacidad

Esta carpeta es una estructura vacía de preparación. El corpus real se mantiene
fuera de Git en almacenamiento autorizado. No copiar audio, transcripciones ni
consentimientos personales a esta carpeta. El esquema no es un permiso de uso.

1. El custodio crea lote inmutable con ID, fecha, hashes, acta de autorización,
   finalidad, permisos separados de evaluación/entrenamiento/publicación, política
   de retención y acceso mínimo. Archivos privados en directorio 0700/archivos 0600.
2. Separar identificación/consentimiento, audio, texto ASR, transcripción humana
   literal y ficha comercial ideal. El hash liga el mismo audio; el guion nunca
   rellena una referencia humana. No ejecutar el CLI ASR efímero sobre un original:
   su contrato elimina el archivo de entrada.
3. Reutilizar doble escucha/adjudicación de #28. La persona que transcribe no ve
   ASR/guion. Las dudas se reescuchan y registran en acta; especialistas distintos
   revisan entidades y relaciones comerciales. No simular revisores/actas.
4. Usar IDs anónimos para caso, familia de paráfrasis, plantilla, hablante y sesión.
   Padres V1 test quedan excluidos del desarrollo. Piloto ya abierto es diagnóstico;
   no renombrarlo external_test. Separar grupos por fuente, hablante/sesión y
   variantes antes de experimentar. Buscar similitud adicional y revisar los pares:
   los detectores mecánicos no garantizan independencia semántica.
5. Validar un JSONL privado con `python -m training.closure_v2.oral /ruta/privada/lote.jsonl`.
   Rechazos se muestran sin texto sensible. `origin=SINTETICO_ORAL` conserva origen,
   nunca contiene audio/sesión humana ni se usa como test externo humano. Datos
   reales necesitan referencias de autorización/retención/privacidad; transcripción
   humana requiere acta y declaración de escucha. Ningún check certifica esos hechos.
6. Entidades usan offsets Unicode Python [start,end), 24 etiquetas vigentes, sin
   solapes y con alineación spaCy. Negación, capacidad, cantidades internas y ámbitos
   se revisan aparte; no inventar clases o relaciones ni normalizar cifras dudosas.
   Para JSON/relaciones usar referencias comerciales adjudicadas y sus hashes;
   este esquema solo valida ingesta/NER, no acredita semántica ni GOLD.
7. Congelar lote y versiones/hashes de código, esquema, anotaciones y modelos antes
   de comparar. Datos nuevos posteriores forman otro lote: no anexar a V1 ni cambiar
   test para ajustar. Los permisos deben revisarse antes de publicar cualquier derivado.
8. Calcular WER solo con referencia humana legítima del mismo audio y autorización
   verificada, usando normalización declarada y scorer de #28/#23 (S/D/I/N). Sin esos
   elementos devolver NOT_EVALUABLE/null. No mezclar WER de demo/TTS con voz real.

El detector de email/número largo es una defensa adicional: puede dar falsos
positivos y omitir nombres/domicilios. Se requiere revisión humana de privacidad.
Las referencias a actas son aliases opacos; no incluir datos identificables en ellas.
No se evalúa ni se exporta test externo desde este paquete. Su custodio conserva
las referencias cerradas y entrega únicamente resultados agregados autorizados.
