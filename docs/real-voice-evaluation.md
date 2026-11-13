# Evaluate real-voice recordings without modifying source audio

Use the repository runner to preserve a baseline before tuning extraction rules.
The model, references, source files and controlled catalog fixture are hashed;
raw transcription and paired ASR/reference NLP outputs are saved for every case.

## Run locally

To audit a local corpus without touching its recordings:

```bash
.venv/bin/python -m tools.evaluate_real_voice \
  --corpus "$CORPUS" --output "$CORPUS/evaluaciones/baseline-new" \
  --model "$HOMEX_ASR_MODEL_PATH" --values "$CATALOG_FIXTURE"
```

`--values` is a JSON list of public `CatalogValue` records from a controlled
fixture, not a production database. The output directory must be new. `--resume`
requires matching source, model, reference, fixture, package and audio identities.
Each case preserves the raw transcription, reference-input and ASR-input NLP,
original hashes, timing and script-relative WER/CER. Audio is passed through a
private disposable copy because the ASR service consumes its input file.

These discrepancies are not verified spoken-reference accuracy; reference-input
NLP is not a gold oracle. Annotate supported fields independently, review doubtful
audio, and report all 120 recordings as development data if they inform fixes.

## Baseline discipline

Use the original source revision for a baseline. A run against modified rules is
a candidate evaluation, not a reconstruction of the original baseline. Resolve
commercial categories from the manifest/reference metadata, not folders or ID
prefixes. Corpus classification corrections must retain their own history and
must not be counted as NLP improvements.

Case output separates execution completion from pending human audio/field review.
Do not claim full commercial accuracy or independent generalization from these
script-relative metrics. Keep audio/model files and commercial source data out
of Git; retain them in the user's evaluation directory.
