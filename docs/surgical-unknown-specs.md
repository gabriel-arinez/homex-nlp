# Preserve unmapped technical descriptions for review

Unknown technical terms remain literal review evidence and observations, not new catalog references or canonical materials. This change reuses `ESPECIFICACION`, `UNRESOLVED`, `item.unresolved`, and `item.observations`; contracts and the finite lexicon are unchanged.

## Supported evidence

| Spoken example | Retained literal evidence | Not inferred |
| --- | --- | --- |
| `una mesa de MDF enchapado con acabado poliuretano` | `enchapado`; `acabado poliuretano` | Veneer species, coating reference, or a new substrate |
| `una mesa marca Xylotron color qhantati` | `marca Xylotron` | Active brand identifier or a known color |
| `un escritorio de corcho` | `de corcho` | Canonical material identity or commercial reference |

MDF remains the existing explicit material. Unknown colors continue through the existing unresolved-color mechanism.

## Deliberate boundaries

- Brand retention requires the explicit `marca` cue and stops before color, model, dimensions, price, or another structural clause. It preserves the complete bounded literal brand clause, including nominal connectors and numeric brand tokens, without selecting an alternative.
- Unknown material descriptions require a direct main-furniture `de` complement or an explicit `material(es)` cue. At most three descriptive words are retained; their material classification remains unknown.
- Existing known materials/accessories and numeric, capacity, model, price, and negated clauses are not promoted to unknown positive specifications.
- Enchapado morphology and polyurethane finish phrases are preserved as descriptions, without expanding the material lexicon.
- This is bounded clause retention, not copying the transcript into structured observations. The original transcription always remains available for unsupported or longer descriptions.

## Verification

`tests/unit/test_surgical_unknown_specs.py` exercises the public `RulesEngine`, exact literal offsets, unresolved references, observations, negative controls, and preservation of existing commercial quantity, dimensions, color, and price. Existing alternative-clause color abstention remains unchanged.

## Existing ambiguity limits

`Una mesa marca Casa de Muebles del Sur color negro.` still abstains because the existing product parser sees multiple furniture nouns. `Una mesa marca Acme 2000 por quinientos bolivianos.` retains the full brand clause but preserves the existing price abstention rather than inventing a 500 BOB suggestion. Neither product admission nor monetary parsing is changed; the complete original transcript remains available for review.

Drawer words immediately following an explicit `marca` or `modelo` cue are descriptive values, not physical drawer components or accessories.

These tests do not establish frozen-corpus metrics, consumer form integration, release distribution, CI, or deployment. The observations field uses the existing contract; downstream closure remains a separate task.
