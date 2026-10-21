# PRF-04 — evaluación de dominio y dictados de vendedores

**Estado:** preparación técnica implementada; evaluación de campo y aprobación de dominio **no realizadas**.
Este documento no transforma los 675 ejemplos sintéticos preanotados en referencias humanas.
No se promueven B/C ni se cambia `RULES_ONLY` automáticamente.

## 1. Revisión independiente de dominio

Solicitar al responsable comercial y a una persona distinta de quien generó las anotaciones:

1. Revisar una muestra de los 380 muebles autorizados, con trazabilidad por ID y resultado `aprobado / corregido / descartado`. Documentar reglas de cantidad comercial e interna, ejes, unidades, componentes, grupos, moneda y total frente a unitario. No ajustar contra `test`.
2. Crear un conjunto **nuevo y separado**, no derivado de plantillas train/dev/test, que incluya dictados espontáneos, correcciones, negaciones, materiales ambiguos, medidas sin ejes/unidades, varias líneas comerciales y productos fuera del alcance.
3. Anotar por duplicado y resolver desacuerdos antes de ejecutar A/B/C, conservando versión y firma del conjunto de referencia. Mantener separados negativos y positivos; no incorporar las respuestas de ningún motor a la anotación humana inicial.
4. Ejecutar A/B/C sobre el conjunto cerrado, comparar NER por entidad y resultados comerciales/estructurales, falsos positivos, relaciones, JSON exacto, advertencias y reemplazos inválidos. Registrar el denominador, errores y límites. **No aceptar 1,0 en datos preanotados como validación externa.**

## 2. Prueba de campo autorizada

Medir el procedimiento manual y la captura asistida con los mismos tipos de muebles, registrando orden de ejecución para controlar aprendizaje. Solo usar sesiones voluntariamente autorizadas, con transcripción de referencia revisada y sin datos personales en los informes.

Por cada sesión conservar **fuera de Git** un JSONL con `id_sesion` anónimo, `autorizada: true`, `fuente: "DICTADO_VENDEDOR"`, `revisor_dominio`, `transcripcion_referencia`, `transcripcion_asr`, `tiempo_manual_seg`, `tiempo_asistido_seg`, `correcciones`. Opcionalmente: `estructura_referencia` revisada y `variantes` con exactamente `A_RULES_ONLY`, `B_NER_ASSEMBLER`, `C_HYBRID_EXPERIMENTAL`; estas salidas se generan offline y nunca se usan para crear el referente humano.

Ejemplo **solo de formato, no dato de evaluación**:

```json
{"id_sesion":"ANON-001","autorizada":true,"fuente":"DICTADO_VENDEDOR","revisor_dominio":"REV-001","transcripcion_referencia":"Un escritorio con dos cajones","transcripcion_asr":"Un escritorio con tres cajones","tiempo_manual_seg":120,"tiempo_asistido_seg":70,"correcciones":1}
```

Ejecutar exclusivamente sobre datos autorizados reales:

```bash
cd "$HOME/HOMEX/homex-nlp"
uv run python -m training.evaluar_campo_prf04 \
  "$HOME/Descargas/prf04-sesiones-autorizadas.jsonl" \
  --output "$HOME/Descargas/prf04-evaluacion-campo.json"
```

La herramienta computa WER micro por distancia de edición y mediana de tiempos, rechaza sesiones declaradas sintéticas/no autorizadas, IDs duplicados y metadatos incompletos. Su comprobación automática de `autorizada` y `revisor_dominio` **no demuestra consentimiento ni independencia reales**: deben acreditarse fuera del sistema.

## 3. Criterios para autorizar el cierre

- El revisor comercial firma las referencias y documenta desacuerdos; el conjunto de prueba permanece sellado e independiente.
- Se presentan WER, correcciones y productividad con denominadores reales, errores por segmento y límites del estudio. Los umbrales de aceptación los acuerda HOMEX a partir del baseline real, **no de muestras sintéticas**.
- Se demuestra seguridad de negativos/ambiguos y no regresión del flujo de un único mueble.
- B/C solo se promocionan por aprobación expresa y comparación auditada; hasta entonces sigue `RULES_ONLY`.
- Solo después de esas autorizaciones corresponde considerar `main` y ejecutar CI post-merge en NLP, backend y frontend.

**Resultado actual:** las pruebas automáticas de reglas y del evaluador son gates de implementación, no la revisión humana ni un estudio ya concluido.
