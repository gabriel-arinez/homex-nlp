# Controlled real-voice ASR experiments

Keep the original Small CPU/int8 frozen transcripts as the baseline. The new
runner never edits recordings or production decoding settings and uses only the
installed local model. All120 cases are development data, not a held-out study.

## Configurations registered before execution

| Configuration | Single-factor contrast |
|---|---|
| temperature_zero | Frozen production fallback defaults versus forced0.0 |
| no_previous | temperature_zero, with previous-text conditioning disabled |
| vad_no_previous | no_previous, with VAD and500ms silence threshold |
| wider_beam | no_previous, beam8 instead of5 |
| context_no_previous | no_previous, one global technical vocabulary hint |

The context hint contains only generic materials/accessories/currency words,
never scripts, corpus identifiers, source-only product codes or reference answers.
The forced-temperature variants are deterministic decoding experiments, not
assertions of what the speaker said. Signal RMS/low-energy/full-scale statistics
are diagnostics; they are not human speech or clipping adjudication.

```bash
HF_HUB_OFFLINE=1 .venv/bin/python -m tools.experiment_real_voice_asr \
  --corpus "$CORPUS" --model "$HOMEX_ASR_MODEL_PATH" --output "$NEW_OUTPUT"
```

The output directory is exclusive; `--resume` requires the same model/configuration,
runner/reference/audio identities. Every experiment saves segments, effective
options, probabilities, script-relative raw WER/CER, CPU/wall time and process peak
RSS. The original WAV/AAC hashes are checked before and after. Failed cases remain
in the experiment inventory. No production adoption is implied by a lower WER.

Evaluate field recovery separately across original/candidate ASR × original/new
NLP. Keep numeric-normalized discrepancy metrics separate from raw WER and from
human-acoustic validation. Installed faster-whisper1.2.1 signature/source controls
available parameters; official versioned documentation:
https://github.com/SYSTRAN/faster-whisper/tree/v1.2.1
