# Open-vocabulary commercial names

Catalog naming accepts short descriptive phrases with productive adjective
morphology or a proper-name complement, without requiring their
product noun to appear in a product dictionary. Explicit naming declarations
also work inside seller introductions, including `producto llamado`,
`producto nuevo`, `nombre comercial es`, and `se llama`.

## Evidence and boundaries

All names pass through the existing candidate collector: source spans, stable
candidate IDs, explicit negations, corrections, and contradictory values use the
same rules as existing catalog fields. A contradictory or negated explicit name
must not trigger a second implicit-name extraction that fabricates agreement.
Existing category conflicts still require human review.

Natural introductions delimit a following `con` feature or recognized material
clause. `Corrijo el nombre a ...` uses the same cue for extraction and eligibility.
Negated attributes do not supply positive implicit-name evidence (uppercase MDF
is not, by itself, a proper-name complement). Existing
explicit labels remain authoritative for literal names such as
`nombre: Mesa con estilo`. Unlabeled names retain the existing technical and
commercial boundaries. Observations extraction is unchanged.

## Microphone checks and ambiguity

Unlabeled greetings, counting, microphone checks, and recognizable conversational
sentence shapes do not establish commercial identity. These are contextual
utterance patterns, not global forbidden words: `Silla Probando` and
`Nombre comercial: Micrófono Aurora` remain valid names.

An explicit declaration such as `Producto: prueba de voz` or `Nombre: prueba`
retains its proposed name and accepted source evidence, with an
`AMBIGUOUS_COMMERCIAL_NAME` human review referencing that evidence. Acceptance
means an extracted proposal, not proof of the seller's commercial intent.
A product reference such as `El producto tiene ruedas` is not a naming declaration.

## Scope and limitations

This is a deterministic open-vocabulary heuristic, not a Spanish noun-phrase
parser or an independent intent classifier. Unknown short descriptions can still be
ambiguous outside the covered conversational patterns. Novel standalone words
need an explicit naming declaration; existing recognized short product names
remain supported. Repetition and word count alone are not positive evidence;
unfamiliar phrases lacking descriptive morphology need an explicit naming
declaration. This conservative fallback can omit legitimate noun–noun compounds
and is reported as a limitation rather than universal recognition. No model, dependency, or catalog schema was added.

## Verification

Run `tests/unit/test_commercial_names_0130.py` together with the existing catalog,
semantic-v2, and Sourcery catalog suites. They verify exact spans, stable IDs,
accepted/rejected/unresolved decisions, review evidence references, natural
introductions, category conflicts, corrections, legacy names, and abstentions.
