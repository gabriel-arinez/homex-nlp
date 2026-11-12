# Review original voice recordings locally

Generate a private, self-contained `review.html` to compare original recordings, script/document evidence, frozen ASR, and historical/previous/candidate NLP. All cases and fields begin **PENDIENTE**. This is a DEVELOPMENT adjudication queue, not an acoustic accuracy report.

## Quick path

```bash
.venv/bin/python -m tools.review_commercial_voice \
  --corpus /path/to/HOMEX_Guiones_Evaluacion_Voz \
  --references /path/to/references-v2 \
  --baseline /path/to/baseline-routing-v2 \
  --comparison /path/to/comparison-v5 \
  --output /path/to/new-review-output
```

Open the generated `review.html` directly as a local file in a browser. Select WAV or the original AAC, or seek to an ASR segment. Segment timestamps are **not forced script alignment**. AAC codec availability depends on the browser; WAV is the compatible alternative. There is no server, remote asset, analytics, or network request. Original paths must resolve inside `--corpus`, with SHA-256 matching the frozen baseline ledger. Inputs are read-only; existing output is refused.

`--candidate /path/to/new-comparison` optionally adds another comparison-v5-shaped root. Both comparison roots require `cases/original__baseline_nlp/ID.json` and `cases/original__current_nlp/ID.json` for historical inputs; the candidate only uses `original__current_nlp`. Labels keep historical b851, previous 0.1.22, and candidate separate; complete artifact identities and hashes remain inspectable. These labels describe the supplied artifacts, not a newly executed NLP model.

## Human review

1. Inspect the evidence and original audio. Textual priority flags suggest review order; they do not prove acoustic errors.
2. Choose an existing datum or add a new field, including missing/unsupported values. Enter a JSON scalar (`null`, a number, or quoted text), unit, axis, component, modality, correction reason, uncertainty, reviewer, and evidence note.
3. Select the evidence provenance: `SCRIPT_TEXT`, `DOCUMENT_TEXT`, `AUTO_PROPOSAL`, or `HUMAN_AUDIO`. Audio decisions require a finite interval inside the recording and an explicit listening declaration, retained as `listening_attested: true` in exports. Imports missing that flag are rejected, not silently promoted to acoustic evidence. This is **self-reported human review**, not authenticated or machine-certified listening.
4. Export the JSON history separately from audio and source files. Unsaved changes prompt before leaving. Verify the browser download exists; the utility cannot guarantee that a download was saved.

Imports validate schema, fingerprint, source hash, case, field key/type, status, provenance, scalar value, and audio intervals. Duplicate semantically identical identities deduplicate even after JSON object-key reordering; a changed decision with an existing identity rejects the entire import. Independent conflicting decisions remain in the visible history, never silently replacing earlier evidence. The UI does not automatically resolve them or convert textual matches into acoustic confirmation.

For CLI validation/inclusion, add `--annotations /path/to/commercial-human-review.json` and choose a **new** output. No original file or imported export is modified. `review.json` contains all 14 reference field types, null/unsupported placeholders, original evidence, full NLP, category counts, input hashes, and the pending queue. No commercial precision metric is calculated.

## Privacy and boundaries

Generated output includes absolute local audio links, scripts, documents and full results: **keep it private and outside Git**. Human exports also contain commercial values and reviewer names. Only the tool, tests, and this guide are intended to be versioned. The browser CSP denies network connections and permits only hashed inline scripts/styles and local audio. Strings render through `textContent`; embedded JSON escapes HTML delimiters. There is no production frontend/backend integration, model execution, dependency change, or source-file rewrite.

## Verification

```bash
.venv/bin/python -m pytest -q tests/evaluation/test_commercial_review.py
.venv/bin/ruff check tools/review_commercial_voice.py tests/evaluation/test_commercial_review.py
.venv/bin/ruff format --check tools/review_commercial_voice.py tests/evaluation/test_commercial_review.py
```

Synthetic test annotations are not corpus annotations. Real listening, component associations, catalogue truth, unresolved source ambiguities, and conflicting human decisions remain manual work.

The optional browser regression accepts only a separately generated **one-case
synthetic** workspace and a synthetic review export; it refuses the actual
120-case workspace. It verifies key-order-independent identity deduplication,
changed-identity rejection and unchanged history through the browser interface:

```sh
node tests/evaluation/commercial_review_browser_probe.cjs \
  /path/to/synthetic-review/review.html /path/to/synthetic-export.json \
  /path/to/installed/node_modules/@playwright/test
```

Node/Playwright are test tools only, not new Python or production dependencies.
