# Furniture review corrections

The focal fixes preserve source text and candidate offsets, avoid unsupported commercial lines, and retain ambiguity instead of manufacturing certainty. The extraction request now rejects text over **20,000 Unicode characters** with a contract validation error; it never truncates input. This matches the existing catalogue request ceiling and is well above the measured original ASR/script maximum of 645 characters.

## Review findings

| Finding | Observed outcome and correction |
| --- | --- |
| Accessory lookup growth | Count exclusions now inspect bounded local context instead of searching the full prefix for every accessory. Both adjacent count scans are bounded to 200 characters. |
| Comma reference merging | A bare comma no longer proves a product reference. Definite references, explicit composition, integrated names, and established sentence-separated references remain supported. |
| Missing casillero component | Explicit `Escritorio con casillero` retains a component and its literal evidence, not a second commercial line. |
| Counted drawer composition | `con una cajonera` and `con dos cajoneras` describe composition. Their count never replaces the principal furniture quantity; independent drawer orders still require review. |
| Adjacent dimensions | Separate directional scans retain each explicitly valued axis without consuming the preceding dimension as an inverse measurement. The adjective guard still rejects height inferred from `Armario alto de 80 cm de ancho`. |
| Alleged price/count confusion | The tested `USB a 20 BOB` and `USB a 20` already abstained; `4 HDMI a 30 BOB` already retained the explicit count 4, not the price 30. Preserve those behaviors. The actual missing explicit count `USB, 2 unidades` now yields 2. |
| Compound corrections | Correction counts reuse the strict existing commercial cardinal grammar, not an expanded global legacy lexicon. Superseded internal accessory-count evidence is retired as well. Different counted products remain reviewable. |

## Contract and evidence

- `ExtractionRequest.text` accepts empty input through exactly 20,000 characters and rejects longer text during validation. Only the generated extraction-request schema changes; response and transcription schemas do not change.
- `text_original` and source offsets are checked through the public `RulesEngine.extract` interface.
- Component count evidence uses the existing contract; no unsupported component quantity property or separate furniture line is invented.
- `Dos mesas, una de madera y otra metálica` retains unresolved descriptive references and a review warning rather than silently pretending the descriptions are identical.

## Verification

The first public regression run produced **16 failures / 16 passes**, demonstrating the reproduced gaps and working controls. After fixes, the focal and directly related tests pass **142 tests**; broader shared measurement, money, quantity, accessory, negation and internal-correction regressions pass **577 tests**. Scoped Ruff and generated-schema checks pass.

A baseline differential over 46 public inputs preserves 45 outputs exactly, excluding only NLP latency. The remaining intentional difference rejects stale accessory-count evidence after an existing internal correction; its item projection is unchanged and a regression test pins the corrected evidence. No other output difference was observed.

Run the controlled benchmark with `python tools/benchmark_accessory_context.py`. Each length has three repetitions and repeated explicit accessory counts. It is diagnostic, not a wall-clock CI threshold. The structural regression checks that count exclusion no longer searches the entire prefix.

| Characters | Mentions | Baseline / candidate median-time ratio |
| ---: | ---: | ---: |
| 1,000 | 111 | 1.23× |
| 5,000 | 555 | 1.58× |
| 10,000 | 1,111 | 2.22× |
| 20,000 | 2,222 | 2.81× |

Machine-local raw reports are stored outside the repository under the authorized `evaluaciones/sourcery-review-v1/furniture-fix-v1` and `logs/sourcery-review-v1/furniture-fix-v1` evidence directories. These results do not claim corpus-wide quality improvement, acoustic correctness, installed-wheel identity, backend/frontend compatibility, or final release readiness; those checks belong to the parent feature's remaining verification.
