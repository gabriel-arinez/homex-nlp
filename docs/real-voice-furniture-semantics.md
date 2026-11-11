# Conservative furniture semantics

The real-voice continuation distinguishes descriptive product references from independent orders. A bare descriptive clause can refer back to the primary product or an explicitly introduced drawer unit. A separate determiner, count or independent product still requires review; repeated ASR paragraphs are not silently deduplicated.

Drawer references are merged only after clause-local attribute association. Evidence and component references are remapped together. Materials, measurements and accessory quantities are not propagated to unrelated components.

A preceding adjective such as `armario alto` does not override the explicit axis after the same measurement. Unitless spoken measurements retain their scalar and a missing-unit warning. A preceding centimetre measurement does **not** justify inventing centimetres for the following axis. The original final-unit enumeration rule remains unchanged.

Electrical accessories include USB, HDMI and connectors. Counts require an explicit adjacent integer or an explicit count delimiter; protocol numbers such as USB3.0 are not quantities. Conflicting counts remain unresolved. The narrow ASR variant `presiunitario` is recognized as an explicit unit-price label, retaining original evidence. Geometry is never money.

## Verification

- Initial regression suite:7 failures,5 passes before implementation.
- First full suite caught3 regressions: ambiguous compound truncation, incomplete axis-first words, and unsafe unit inheritance. These were removed rather than weakening existing tests.
- Final suite at the semantic source checkpoint:871 passed.
- Focused probes: `python -m pytest -q tests/unit/test_furniture_semantic_v2.py`.
- All120 cases are development data. Textual scalar agreement does not establish acoustic or component-association accuracy.

Risk: item3 (shared parsing and evidence consumers). Independent verification and installed-wheel integration remain required before delivery.

Explicit `acero` and metallic adjectives are evidence, not inferred steel grades. A material adjective inside a component name (for example `patas metálicas`) belongs to that component. Board material and thickness remain attached to the board. Two additional regressions failed before this correction; all812 unit/contract cases then passed.
