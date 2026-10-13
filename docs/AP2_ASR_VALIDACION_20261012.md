# AP2 — Validación ASR, evidencia y borrado temporal (12/10/2026)

## Línea base

CI de `main` [38330659108](https://github.com/gabriel-arinez/homex-nlp/actions/runs/38330659108): **3/3 jobs correctos**; suite principal **58 passed (1.12 s)** más **14 passed** en comprobación de distribución/consumidor. Incluye contratos, corpus, rueda y runtime F10.

## Hallazgos comprobados y solución

1. **Inicio temporal negativo aceptado por `TranscriptSegment`**. El contrato solo comparaba fin e inicio; el nuevo test `test_ap2_no_permite_timestamps_negativos_o_invertidos` exige rechazo de inicio negativo sin cambiar versión `1.0` (precisión semántica del contrato). `TranscriptionResult` mantiene rechazo de solapes y fin superior a la duración.
2. **Directorio recibido como ruta de audio**. `validate_audio_file` produce `AUDIO_INVALID`, pero el `finally` anterior intentaba `unlink` sobre directorio y lo reemplazaba por `IsADirectoryError`. Se protege directorio real sin debilitar el borrado de archivos ni enlaces simbólicos rechazados.
3. **Fallos parciales de transcriptor/timeout**. Test nuevo con generador que produce primer segmento y después falla: exige `TRANSCRIPTION_FAILED`, `retryable` y archivo temporal eliminado. Audio vacío/excesivo se rechaza sin invocar modelo; symlink se retira sin borrar destino.

Tests: `tests/unit/test_ap2_asr_boundaries.py` y suite anterior `tests/unit/test_asr_service.py`.

## Reproducibilidad

```bash
uv sync --locked --extra dev --extra asr --python 3.11.15
uv run --locked pytest -q tests/unit/test_ap2_asr_boundaries.py
make check
make distribution-check
make f10-check
```

Prohibido persistir texto de voz o ruta temporal como evidencia de CI. Futuros flujos de HITL en AP5 deberán probar idempotencia completa por captura e incorporación, corrección humana y compatibilidad de contratos en backend; no cambiar esquema por adelantado.
