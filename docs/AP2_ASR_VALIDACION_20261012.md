# AP2 — Validación ASR, evidencia y borrado temporal (12/10/2026)

## Línea base

CI de `main` [38330659108](https://github.com/gabriel-arinez/homex-nlp/actions/runs/38330659108): **3/3 jobs correctos**; suite principal **58 passed (1.12 s)** más **14 passed** en comprobación de distribución/consumidor. Incluye contratos, corpus, rueda y runtime F10.

## Hallazgos comprobados y solución

1. **Inicio temporal negativo ya estaba prohibido** por el tipo Pydantic `DecimalText` (expresión regular). El nuevo test `test_ap2_no_permite_timestamps_negativos_o_invertidos` lo demuestra explícitamente, sin duplicar validaciones ni cambiar contrato `1.0`. `TranscriptionResult` mantiene rechazo de solapes y fin superior a la duración.
2. **Directorio recibido como ruta de audio**. `validate_audio_file` produce `AUDIO_INVALID`, pero el `finally` anterior intentaba `unlink` sobre directorio y lo reemplazaba por `IsADirectoryError`. Se protege directorio real sin debilitar el borrado de archivos ni enlaces simbólicos rechazados.
3. **Fallos parciales de transcriptor/timeout**. Test nuevo con generador que produce primer segmento y después falla: exige `TRANSCRIPTION_FAILED`, `retryable` y archivo temporal eliminado. Audio vacío/excesivo se rechaza sin invocar modelo; symlink se retira sin borrar destino.

Tests: `tests/unit/test_ap2_asr_boundaries.py` y suite anterior `tests/unit/test_asr_service.py`.

## Integridad interrepositorio F10 preservada

El wheel `vendor/homex_nlp-0.1.0-py3-none-any.whl` del backend está fijado por SHA-256 y NO se modifica. El gate `tools/verify_backend_f10.py` ahora contrasta ese wheel con el código de su commit de origen **`b5fe2921320c9031f6d44dc5c91a18411daa393e`** (F06), no con `HEAD` de desarrollo. En GitHub Actions se obtiene ese histórico con `fetch-depth: 0`. El código NLP nuevo continúa sujeto a `make check` y `make distribution-check`; así ambas invariantes se verifican, sin aparentar que F10 consumió la corrección AP2.

**Operativamente**, el fix de directorio estará disponible cuando se cree y valide un **nuevo artefacto NLP** consumido por backend mediante release coordinada y autorizada. El wheel F10 en uso permanece inmutable; AP2 no promociona código nuevo a RC2/producción.

## Reproducibilidad

```bash
uv sync --locked --extra dev --extra asr --python 3.11.15
uv run --locked pytest -q tests/unit/test_ap2_asr_boundaries.py
make check
make distribution-check
make f10-check
```

Prohibido persistir texto de voz o ruta temporal como evidencia de CI. Futuros flujos de HITL en AP5 deberán probar idempotencia completa por captura e incorporación, corrección humana y compatibilidad de contratos en backend; no cambiar esquema por adelantado.
