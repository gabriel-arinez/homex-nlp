# Initial diagnosis reconstructed from frozen baseline evidence

The initial 120-case execution completed before any extraction-rule changes. This
report indexes its immutable outputs; it is not independent audio adjudication.

## Baseline

| Repository | Branch at start | Exact HEAD |
|---|---|---|
| homex-nlp | main | c94e7a89995a7157bd113a03bb8304321d30b0b1 |
| homex-backend | main | ee6c80f13ff76e23c4c572c81042a0b9760db033 |
| homex-frontend | main | ecb7f23b4d7f25317ae1501733cc8c915bed63c1 |

NLP started with untracked `.atl/`, preserved. Other two repositories clean.
Effective NLP0.1.21, faster-whisper1.2.1, CTranslate2 4.8.2, spaCy3.8.13,
Pydantic2.13.4, Python3.11.15. Whisper Small CPU/int8 with Spanish language;
other inference parameters are faster-whisper defaults. Exact model-file hashes
and source hashes are in baseline/identity.json. ASR service/CLI consume input
paths; evaluation uses disposable copies. AAC is not directly supported by its
validator, so previously verified PCM16/mono/16kHz WAVs are used.

Backend Django5.2.17/DRF3.18.2 uses a vendored NLP0.1.21 wheel. Frontend installed
Vue3.5.42, Vite8.3.4, Vitest4.1.12, TypeScript6.0.3, Playwright1.63.0,
Node24.18.1 (see final-parent-spotcheck log). Lockfiles/HEAD define exact source.

## Input audit

120 unique matching manifest/reference/source IDs; 120 AAC and120 WAV.
Seven confirmed sillones reclassified OTRO, with immutable metadata backups.
Current grouping76 furniture/27 chairs/7 floor/10 OTRO remains PROVISIONAL pending
business confirmation of three poltronas. Folders/ID prefixes are not categories.
All240 audio hashes and source/reference scripts preserved. Historical reading
DOCX/group documents are not relabeled; they are historical recording artifacts,
not authoritative routing. Source metadata issues (35 recorded) remain traceable.
Family/exact duplicate groups are recorded separately; nothing was deleted.

## Flow and responsibilities

NLP AsrService -> FasterWhisperAdapter, segment consumption -> verbatim transcript.
Backend apps/capturas/asr.py caches model by process, serializes lazy inference;
pipeline.py stores transcript, deletes its temporary audio, invokes category
extractor, validates and projects proposal. Furniture uses AdaptadorNLP and
PRF04 projection; catalog uses CatalogRequest with active dictionary records and
ProductoSerializer field validation. Backend computes authoritative totals and
stock; NLP is a suggestion only. Frontend CapturaCatalogo applies supported fields
to ProductoForm; CapturaAsistida/configurator mapper handles custom furniture.
A valid JSON alone is not proof of useful form application.

## Baseline findings

See baseline/summary.json for category WER/CER; raw cases retain both reference-input
and ASR-input extraction. Global script-relative WER1495/6627=22.5592%,
CER7758/42777=18.1359%. Digit-vs-word number spellings count as text edits even
where commercial meaning is unchanged (e.g. MP0001), so these rates are NOT
commercial error rates. Reference audio adjudication remains pending.

Observed lexical/grammar gaps and safe bounded fixes are in root-cause-matrix.
NO_PROPOSAL/multiple-product cases must not all be assigned one presumed cause.
No model/dependency/public schema was changed for this checkpoint.
