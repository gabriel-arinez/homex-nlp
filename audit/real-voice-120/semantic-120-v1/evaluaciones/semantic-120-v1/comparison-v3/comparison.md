# Four-cell development comparison

| ASR / NLP | Cases | Matched / expected scalar tuples | No proposal | Original WER errors/words | Strict WER errors/words |
| --- | ---: | ---: | ---: | ---: | ---: |
| no_previous__baseline_nlp | 120 | 433/1087 | 23 | 1470/6627 | 846/6371 |
| no_previous__current_nlp | 120 | 483/1087 | 17 | 1470/6627 | 846/6371 |
| original__baseline_nlp | 120 | 438/1087 | 23 | 1495/6627 | 922/6371 |
| original__current_nlp | 120 | 486/1087 | 17 | 1495/6627 | 922/6371 |
| temperature_zero__baseline_nlp | 120 | 432/1087 | 24 | 1579/6627 | 1007/6371 |
| temperature_zero__current_nlp | 120 | 480/1087 | 18 | 1579/6627 | 1007/6371 |

## Contract-supported scalar field families

Unsupported category fields remain in full-coverage rows, not in this denominator. Chair feature subtypes and catalog context may still restrict realizable values. These are not association/precision metrics.

| Input / NLP | Supported matched / expected |
| --- | ---: |
| no_previous__baseline_nlp | 433/1000 |
| no_previous__current_nlp | 483/1000 |
| original__baseline_nlp | 438/1000 |
| original__current_nlp | 486/1000 |
| script_control__baseline_nlp | 439/1000 |
| script_control__current_nlp | 501/1000 |
| temperature_zero__baseline_nlp | 432/1000 |
| temperature_zero__current_nlp | 480/1000 |

## Controlled script-input diagnostic (not ASR or gold)

- script_control__baseline_nlp: 439/1087 scalar tuples; 21 no-proposal cases.
- script_control__current_nlp: 501/1087 scalar tuples; 13 no-proposal cases.

**All120 are development cases; acoustic and association denominators are zero.**

Pending configurations: {"vad_no_previous": {"completed_cases": 105, "expected_cases": 120}}

Headline recall excludes relation, count, modality and currency correctness. Extra predictions are unverified candidates, not confirmed false positives.
