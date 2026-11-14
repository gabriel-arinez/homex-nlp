# Real-voice semantic intervention — verified scope and remaining limits

The engineering intervention improves supported script-scalar coverage on unchanged original ASR, with no lost previously matched scalar tuple in that comparison. This is **not** a completed human-acoustic or full commercial precision evaluation. All120 cases are development data.

Original ASR + baseline NLP: **438/1000** supported scalar tuples; corrected NLP: **487/1000**. Recoveries in 18 cases; scalar-loss cases: 0. No-proposal cases: 23→17.

The denominator deduplicates verified script literals/scalars within each case and excludes unsupported category field families. It does not validate associations, modality, acoustic truth, every feature subtype or precision. OTRO configurator omissions are not NLP defects. Full-coverage and supported denominators are both retained.

## Per-category NLP on unchanged original ASR

| Category | Cases | Before supported matches | After supported matches | Denominator | No proposal before→after |
| --- | ---: | ---: | ---: | ---: | --- |
| MUEBLE_MEDIDA | 73 | 320 | 368 | 767 | 23→17 |
| OTRO | 13 | 20 | 20 | 20 | 0→0 |
| PISO_FLOTANTE | 7 | 20 | 21 | 28 | 0→0 |
| SILLA | 27 | 78 | 78 | 185 | 0→0 |

## ASR experiment register

Raw WER/CER are script-relative, not verified spoken accuracy. Strict numeric-commercial WER is reported separately in comparison-v5; metric-only changes are not recognition gains. Exact parameters/model hashes/segments/tokens/timing/CPU/peak-process-RSS are retained in asr-experiments. Latencies overlap other test workloads.

| Setting | Category | WER errors / words | CER errors / characters |
| --- | --- | ---: | ---: |
| temperature_zero | MUEBLE_MEDIDA | 1126/4174 | 5924/27101 |
| temperature_zero | OTRO | 133/703 | 655/4395 |
| temperature_zero | PISO_FLOTANTE | 93/347 | 382/2313 |
| temperature_zero | SILLA | 227/1403 | 1153/8968 |
| no_previous | MUEBLE_MEDIDA | 1001/4174 | 5447/27101 |
| no_previous | OTRO | 146/703 | 713/4395 |
| no_previous | PISO_FLOTANTE | 94/347 | 384/2313 |
| no_previous | SILLA | 229/1403 | 1149/8968 |
| vad_no_previous | MUEBLE_MEDIDA | 1025/4174 | 5617/27101 |
| vad_no_previous | OTRO | 155/703 | 734/4395 |
| vad_no_previous | PISO_FLOTANTE | 95/347 | 384/2313 |
| vad_no_previous | SILLA | 227/1403 | 1161/8968 |
| wider_beam | MUEBLE_MEDIDA | 984/4174 | 5359/27101 |
| wider_beam | OTRO | 144/703 | 704/4395 |
| wider_beam | PISO_FLOTANTE | 97/347 | 396/2313 |
| wider_beam | SILLA | 229/1403 | 1154/8968 |
| context_no_previous | MUEBLE_MEDIDA | 1220/4174 | 6830/27101 |
| context_no_previous | OTRO | 154/703 | 802/4395 |
| context_no_previous | PISO_FLOTANTE | 109/347 | 458/2313 |
| context_no_previous | SILLA | 234/1403 | 1205/8968 |

No production ASR model/configuration was changed. Candidate selection cannot rely on WER or one favorable case; all five settings have full two-version NLP comparisons.

## Corrections and checks

- Conservative furniture/coreference/component boundaries; preserve real independent-order abstention.
- Axis-adjective disambiguation, unitless spoken scalar evidence without invented units, component-local material/thickness evidence.
- USB/HDMI/interface connector counts, strict compound integers and alternative-count abstention.
- Explicit presiunitario alias, bounded catalog names, reason-bearing spelling equivalence, ambiguous initial de/a abstention, explicit HDF8mm gauge.
- Every defect had observed RED and GREEN regression logs; failed iterations are retained. Final891NLP tests,99backend tests and306frontend tests passed, alongside schemas/lint/format/type/build.
- Actual final wheel consumed from backend site-packages;26modules match the wheel.8/8 actual audio browser cases cover four forms;19 authoritative-model snapshots unchanged;240 original audio hashes unchanged.
- Reproducible0.1.22 wheel identity fixed without overwriting historical0.1.21 artifacts. Exactly two verified historical tokenizer-hash fingerprints exempted; all four source-commit CI jobs green.

## Remaining limits and difficult cases

No proposal on original ASR: MP-0003, MP-0008, MP-0012, MP-0017, MP-0022, MP-0026, MP-0037, MP-0051, MP-0057, MP-0060, MP-0061, MP-0065, MP-0066, MP-0070, MP-0071, MP-0072, MP-0074. See cases-needing-review.json for warnings, all120 pending acoustic/association cases and every full raw result.
MP-0036 keeps its unitless depth and unspecified price pending; MP-0045 does not force composite side geometry into unrelated global axes. Repeated original-ASR passages are not silently erased or treated as genuine duplicate orders. SIL-0016 de43 remains unresolved instead of fabricating D43. New unmatched predictions are review candidates, not confirmed false positives.
Full human field association validation, listening adjudication and independent recordings are unavailable.69 connected commercial/source groups prevent claiming these development examples as a holdout. The independent-audio protocol is in references-v2; no generalization percentage is invented.
Backend consumer commit7040564 is local on its controlled branch; remote publication awaits explicit destination/credential authorization. No frontend source change, main merge or deployment was made.

## Evidence navigation

- latest-evaluation.json: source versions, hashes, denominators, scope and superseded-run index.
- case-matrix.jsonl: all120 IDs with14 comparison cells each; comparison-v5 contains1680 complete raw case results and field expectations/predictions.
- root-cause-matrix.json and comparison-v5/root-cause-isolation.json: contract-supported classifications versus uncertain text-channel/association causes.
- references-v2: all field proposals, document/script/ASR provenance and private timestamped playback index. No automatic transcript is human gold.
- integration-v3 and logs/semantic-120-v1: exact commands, screenshots, raw responses, immutable authority snapshots and complete console output.
- Raw recordings,462 replay clips and full large screencast archives remain local. Public copies sanitize credentials and export text trace events plus final screenshots with an omission/hash ledger.

Risk: items3(shared parsing/evidence consumers) and5(package distribution and consumer version binding). Independent source/installed-wheel and end-to-end checks passed in their documented scope.

## ASR baseline and promotion decision

| Original category | WER errors / words | CER errors / characters |
| --- | ---: | ---: |
| MUEBLE_MEDIDA | 1042/4174 | 5568/27101 |
| SILLA | 227/1403 | 1153/8968 |
| OTRO | 133/703 | 655/4395 |
| PISO_FLOTANTE | 93/347 | 382/2313 |

| ASR setting + corrected NLP | Supported script tuples | Recoveries versus original | Lost previous scalar matches | No proposal |
| --- | ---: | ---: | ---: | ---: |
| context_no_previous | 501/1000 | 34 | 20 | 15 |
| no_previous | 484/1000 | 11 | 14 | 17 |
| original | 487/1000 | 0 | 0 | 17 |
| temperature_zero | 481/1000 | 0 | 6 | 18 |
| vad_no_previous | 497/1000 | 38 | 28 | 14 |
| wider_beam | 489/1000 | 14 | 12 | 16 |

Context/VAD recover additional script-scalar tuples but also lose previous matches. Incomplete acoustic/association gold and unverified extra predictions do not justify a global production change. No per-case cherry-picking or complete reference prompts were used.

Candidate-only literal material evidence and structured applied fields are not interchangeable with full commercial association accuracy. In particular, candidate colors not applied as primary/secondary are not silently counted as usable form colors. Missing fixture catalog values and unspecified price modalities need separate review, not fabricated completion.
See asr-selection.json for CPU/wall/median/max/peak-process-memory and exact decision scope. The original ASR process handle expired after turn interruptions; completion is established by all600 successful case artifacts, final aggregates and240 unchanged audio hashes, not an invented shell exit status.

## Later workspace observation

After integration, original backend acquired an untracked `celerybeat-schedule.db` with a later creation timestamp; ownership is unestablished and it was not touched or published. Historical system-temp worktrees are now absent, but consumer commit7040564 and all evidence remain in Git/corpus. No original source checkout is described as currently clean without this qualification. Use the portable fresh bootstrap rather than vanished temporary paths. See workspace-state.json.
