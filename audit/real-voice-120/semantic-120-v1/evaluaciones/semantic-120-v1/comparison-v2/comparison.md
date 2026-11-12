# Four-cell development comparison

| ASR / NLP | Cases | Matched / expected scalar tuples | No proposal | Original WER errors/words | Strict WER errors/words |
| --- | ---: | ---: | ---: | ---: | ---: |
| no_previous__baseline_nlp | 120 | 421/1087 | 23 | 1470/6627 | 846/6371 |
| no_previous__current_nlp | 120 | 471/1087 | 17 | 1470/6627 | 846/6371 |
| original__baseline_nlp | 120 | 426/1087 | 23 | 1495/6627 | 922/6371 |
| original__current_nlp | 120 | 474/1087 | 17 | 1495/6627 | 922/6371 |
| temperature_zero__baseline_nlp | 120 | 420/1087 | 24 | 1579/6627 | 1007/6371 |
| temperature_zero__current_nlp | 120 | 468/1087 | 18 | 1579/6627 | 1007/6371 |

## Controlled script-input diagnostic (not ASR or gold)

- script_control__baseline_nlp: 420/1087 scalar tuples; 21 no-proposal cases.
- script_control__current_nlp: 482/1087 scalar tuples; 13 no-proposal cases.

**All120 are development cases; acoustic and association denominators are zero.**

Pending configurations: {"vad_no_previous": {"completed_cases": 30, "expected_cases": 120}}

Headline recall excludes relation, count, modality and currency correctness. Extra predictions are unverified candidates, not confirmed false positives.
