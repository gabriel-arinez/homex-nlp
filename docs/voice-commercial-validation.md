# Extract evidence, not forbidden expressions

Catalog extraction uses positive product identity, explicit commercial names and recognized structured attributes. It does not reject a name for containing greeting, testing or microphone-related words, and it has no replacement blacklist or linguistic exceptions.

Category compatibility, valid units/types/values and coherent commercial relationships remain enforced. Text without sufficient commercial evidence produces no proposal; partial valid input produces only evidence-backed attributes. Nothing supplies missing prices, measurements, materials or quantities.

## Scope

General NLP still accepts brief legitimate descriptions such as `silla plegable` and retains its existing 20,000-character input contract. The commercial voice assistant separately enforces at least 15 seconds of audio and 20 words, with a 3,000-character editable-text maximum, in its frontend/backend boundary. Length is not evidence of commercial validity.

Explicit names such as `nombre: Silla Buenas` or `producto: Micrófono Aurora` remain eligible subject to commercial category compatibility. Names are not restricted to a closed catalog vocabulary.

## Observations and provenance

Catalog observations require explicit complementary `observaciones` text with its real source span. Neither a whole-input fallback nor a generic description marker copies the entire dictation into observations. Original/corrected transcriptions remain in capture evidence, not in product notes. Existing manual notes are preserved by the companion form.

## Verification and rollback

Local corrective package: **0.1.29**; no publication implied. New regressions observed RED (18 failed), then focused GREEN (245 passed). Final source and non-editable installed-wheel suites each passed **1,209 tests**; Ruff lint/format and package-byte identity passed. The 120 written scripts and 120 stored real-ASR outputs all pass the assistant's 20-word/3,000-character thresholds. The two existing synthetic four-minute experiments yield 2,807 and 638 characters; real long seller-dictation coverage is not claimed.

Rollback boundary: catalog extraction and its tests, package version/lock, and the companion backend's matching wheel/pins must be reverted together. Historical wheels/checksums were not modified. See `voice-hitl-corrective-verification.md` for the cross-repository verification ledger.
