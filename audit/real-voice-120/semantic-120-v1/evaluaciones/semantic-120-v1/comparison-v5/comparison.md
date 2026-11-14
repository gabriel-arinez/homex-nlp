# Four-cell development comparison

| ASR / NLP | Cases | Matched / expected scalar tuples | No proposal | Original WER errors/words | Strict WER errors/words |
| --- | ---: | ---: | ---: | ---: | ---: |
| context_no_previous__baseline_nlp | 120 | 443/1087 | 22 | 1717/6627 | 980/6371 |
| context_no_previous__current_nlp | 120 | 501/1087 | 15 | 1717/6627 | 980/6371 |
| no_previous__baseline_nlp | 120 | 433/1087 | 23 | 1470/6627 | 846/6371 |
| no_previous__current_nlp | 120 | 484/1087 | 17 | 1470/6627 | 846/6371 |
| original__baseline_nlp | 120 | 438/1087 | 23 | 1495/6627 | 922/6371 |
| original__current_nlp | 120 | 487/1087 | 17 | 1495/6627 | 922/6371 |
| temperature_zero__baseline_nlp | 120 | 432/1087 | 24 | 1579/6627 | 1007/6371 |
| temperature_zero__current_nlp | 120 | 481/1087 | 18 | 1579/6627 | 1007/6371 |
| vad_no_previous__baseline_nlp | 120 | 439/1087 | 21 | 1502/6627 | 878/6371 |
| vad_no_previous__current_nlp | 120 | 497/1087 | 14 | 1502/6627 | 878/6371 |
| wider_beam__baseline_nlp | 120 | 435/1087 | 23 | 1454/6627 | 843/6371 |
| wider_beam__current_nlp | 120 | 489/1087 | 16 | 1454/6627 | 843/6371 |

## Contract-supported scalar field families

Unsupported category fields remain in full-coverage rows, not in this denominator. Chair feature subtypes and catalog context may still restrict realizable values. These are not association/precision metrics.

| Input / NLP | Supported matched / expected |
| --- | ---: |
| context_no_previous__baseline_nlp | 443/1000 |
| context_no_previous__current_nlp | 501/1000 |
| no_previous__baseline_nlp | 433/1000 |
| no_previous__current_nlp | 484/1000 |
| original__baseline_nlp | 438/1000 |
| original__current_nlp | 487/1000 |
| script_control__baseline_nlp | 439/1000 |
| script_control__current_nlp | 501/1000 |
| temperature_zero__baseline_nlp | 432/1000 |
| temperature_zero__current_nlp | 481/1000 |
| vad_no_previous__baseline_nlp | 439/1000 |
| vad_no_previous__current_nlp | 497/1000 |
| wider_beam__baseline_nlp | 435/1000 |
| wider_beam__current_nlp | 489/1000 |

## Controlled script-input diagnostic (not ASR or gold)

- script_control__baseline_nlp: 439/1087 scalar tuples; 21 no-proposal cases.
- script_control__current_nlp: 501/1087 scalar tuples; 13 no-proposal cases.

**All120 are development cases; acoustic and association denominators are zero.**

Pending configurations: {}

Headline recall excludes relation, count, modality and currency correctness. Extra predictions are unverified candidates, not confirmed false positives.
