# Conservative commercial product relations

The deterministic extractor recognizes compound shelving names, explicitly
integrated sideboards, and references to an already introduced drawer assembly.
It still returns a proposal **for review**, not an approved commercial line.
Unsupported or ambiguous product relationships continue to abstain.

## What changed

| Literal evidence | Interpretation | Safety boundary |
| --- | --- | --- |
| `estante librero`, `estantes libreros` | One compound product span | `estante y librero` and alternatives remain separate |
| A desktop followed by `credenza integrada` | Explicit integrated component | A counted independent credenza or unqualified lateral credenza remains unresolved |
| `con cajonería rodante` followed by `cajonera rodante de ...` | Introduced drawer assembly and descriptive reference | A new quantity, `otra`, or independent conjunction is not merged |
| `con cajonera` followed by `incluye cajonera` | Reference to the introduced component | `incluye` alone cannot merge another main product |
| Counted `credencia(s)` with an explicit dimension/unit and furniture material | Literal furniture noun, original spelling retained | Bare or otherwise ambiguous tokens are not repaired |

`Credencia` is documented as furniture by the
[Spanish Ministry of Culture furniture thesaurus](https://tesauros.cultura.gob.es/tesauros/mobiliario/1174823.html).
This lexical evidence supports reading the **text**; it does not establish what
any speaker said. The extractor does not rewrite it as an acoustically verified
`credenza`.

## Evidence and association

Product and component candidates retain the original text spans. Suppressed
product references remain rejected candidates with an explicit reason. Drawer
references merge their component evidence only after ordinary span association.
A contiguous list of already extracted dimensions can belong to that drawer or
an explicitly integrated sideboard; a new sentence/entity or unparsed connector
terminates that association. Existing units, amounts, quantities and component
accessories are not inferred to make a proposal appear complete.

The focused tests cover status, proposal count, commercial quantity/price,
component dimensions/materials, source offsets and the nearest independent or
ambiguous alternatives. Existing standalone furniture remains supported.

## Intentional abstentions

- A set containing differently sized tables needs commercial/component
  adjudication, not flattened dimensions on one table.
- Repeated ASR clauses with fresh explicit quantities do not establish whether
  the speaker repeated an order or requested additional products.
- A cabinet with six doors followed by six cabinets does not establish a
  reliable distinction between compartments and commercial units.
- A lateral credenza without an explicit integration statement remains
  ambiguous between component and independent product.
- An unsupported ASR noun is not repaired from the script or audio expectations.

## Evaluation boundaries

Private evaluation artifacts live under the corpus's new
`evaluaciones/commercial-review-v1` phase; earlier results are not overwritten.
The fresh pre-edit baseline runs all 120 frozen original ASR texts and all 120
scripts through the public extraction APIs. Every meaningful fix group repeats
those 240 inputs, plus the 17 diagnostic cases across the five existing frozen
ASR configurations. No audio is decoded again.

Full raw outputs, text/source/dependency hashes, routing, warnings, timings and
script-relative scalar recovery/loss flags are retained. New proposals and
additional predictions are **review candidates**, not confirmed correct fields
or false positives. Component association is checked with independent synthetic
language probes; scalar matches alone do not establish commercial precision.
All 120 cases remain development data. Human listening and acoustic truth stay
`PENDIENTE` until an actual human decision supplies them.

## Literal component variant and association proof

`credencia integrada` uses the same literal furniture-family relation as
`credenza integrada`; the original component name and offsets are retained.
This is not a guessed audio correction. Its explicitly introduced width, height,
depth and material belong to that component, not to the desktop. One RED and
five passing probes preceded the correction; the six-probe suite also preserves
non-furniture words, unqualified lateral descriptions and independent orders.

The original-ASR case MP-0007 exposed this association defect even though the
scalar-presence metric already found some numeric values. Its malformed desktop
measurement remains unresolved; no script dimension is substituted for the ASR.
No acoustic or full-corpus association accuracy is claimed.
