"""Open-vocabulary commercial names retain literal, auditable evidence."""

import pytest

from homex_nlp.catalog import CatalogRequest, extract_catalog


def extract(text, category="OTRO"):
    result = extract_catalog(CatalogRequest(category=category, text=text))
    assert all(e.text == text[e.start : e.end] for e in result.evidence)
    return result


def assert_name(result, text, name):
    assert result.fields["nombre"] == name
    accepted = [e for e in result.evidence if e.label == "nombre" and e.decision == "ACCEPTED"]
    assert len(accepted) == 1
    candidate = accepted[0]
    start = text.index(name)
    assert (candidate.start, candidate.end, candidate.text) == (start, start + len(name), name)
    assert candidate.candidate_id == f"nombre-{start}-{start + len(name)}"
    assert not any(r.field == "nombre" for r in result.field_reviews)


@pytest.mark.parametrize(
    "name",
    [
        "Espejo decorativo",
        "Armario metálico",
        "Librero modular",
        "Ventana corrediza",
        "Biombo trenzado",
        "Perchero orbital",
        "Silla Probando",
    ],
)
def test_novel_noun_phrases_do_not_require_product_dictionary(name):
    result = extract(name)
    assert_name(result, name, name)
    assert result.fields == {"nombre": name}


@pytest.mark.parametrize(
    "text,name",
    [
        ("Quiero registrar producto: Espejo Aurora", "Espejo Aurora"),
        ("Necesito agregar un producto llamado Librero Atlas", "Librero Atlas"),
        ("El nombre comercial es Armario Boreal", "Armario Boreal"),
        ("Registra un producto nuevo: Organizador Modular", "Organizador Modular"),
        ("Se llama Koru", "Koru"),
        ("Necesito agregar un producto llamado Librero Atlas con ruedas", "Librero Atlas"),
    ],
)
def test_natural_explicit_names_use_exact_name_spans(text, name):
    assert_name(extract(text), text, name)


@pytest.mark.parametrize("text", ["Hola, probando el micrófono", "Uno, dos, tres, prueba de audio"])
def test_pure_microphone_checks_abstain(text):
    result = extract(text)
    assert not result.fields
    assert result.unrecognized == [text]
    assert all(e.decision != "ACCEPTED" for e in result.evidence)


@pytest.mark.parametrize(
    "text,name", [("Producto: prueba de voz", "prueba de voz"), ("Nombre: prueba", "prueba")]
)
def test_ambiguous_explicit_names_keep_proposal_and_human_review(text, name):
    result = extract(text)
    assert result.fields == {"nombre": name}
    candidate = next(e for e in result.evidence if e.label == "nombre")
    assert candidate.decision == "ACCEPTED"
    assert (candidate.start, candidate.end, candidate.text) == (text.index(name), len(text), name)
    review = next(r for r in result.field_reviews if r.field == "nombre")
    assert review.code == "AMBIGUOUS_COMMERCIAL_NAME"
    assert review.severity == "REVIEW"
    assert review.evidence_ids == [candidate.candidate_id]


def test_microphone_is_a_valid_product_identity():
    text = "Nombre comercial: Micrófono Aurora"
    assert_name(extract(text), text, "Micrófono Aurora")


def test_natural_corrections_and_negation_reuse_shared_candidates():
    text = "no producto llamado Espejo Aurora, mejor producto llamado Librero Atlas"
    result = extract(text)
    assert_name(result, text, "Librero Atlas")
    old = next(e for e in result.evidence if e.text == "Espejo Aurora")
    assert old.decision == "REJECTED"
    assert old.reason == "Negación explícita"


@pytest.mark.parametrize("category", ["SILLA", "PISO_FLOTANTE"])
def test_natural_introduction_preserves_category_conflict(category):
    name = "Piso flotante" if category == "SILLA" else "Silla Aurora"
    result = extract("Necesito agregar un producto llamado " + name, category)
    assert "nombre" not in result.fields
    assert any(r.code == "CATEGORY_CONFLICT" for r in result.field_reviews)
    assert next(e for e in result.evidence if e.label == "nombre").decision == "UNRESOLVED"


def test_existing_authoritative_label_keeps_name_with_con():
    text = "nombre: Mesa con estilo"
    assert_name(extract(text), text, "Mesa con estilo")


def test_unlabeled_reference_without_name_does_not_become_an_explicit_cue():
    result = extract("hola producto")
    assert not result.fields
    assert result.unrecognized == ["hola producto"]


@pytest.mark.parametrize(
    "text",
    [
        "Esto es una prueba de voz",
        "Estoy probando el micrófono",
        "El producto tiene ruedas",
        "El producto mencionado",
    ],
)
def test_conversational_sentences_and_product_references_are_not_names(text):
    result = extract(text)
    assert "nombre" not in result.fields
    assert not any(e.label == "nombre" and e.decision == "ACCEPTED" for e in result.evidence)


def test_new_introduction_uses_existing_conflict_and_correction_rules():
    first, second = "Espejo Aurora", "Librero Atlas"
    result = extract(f"producto llamado {first}, mejor producto llamado {second}")
    assert result.fields["nombre"] == second
    assert [(e.text, e.decision) for e in result.evidence if e.label == "nombre"] == [
        (first, "REJECTED"),
        (second, "ACCEPTED"),
    ]
    conflict = extract(f"producto llamado {first}, producto llamado {second}")
    assert "nombre" not in conflict.fields
    assert all(e.decision == "UNRESOLVED" for e in conflict.evidence if e.label == "nombre")
    assert any(r.field == "nombre" and r.severity == "REVIEW" for r in conflict.field_reviews)


@pytest.mark.parametrize(
    "text,name",
    [
        ("producto: Tiene estilo", "Tiene estilo"),
        ("El producto: Anterior Aurora", "Anterior Aurora"),
        ("nombre: Hola Aurora", "Hola Aurora"),
    ],
)
def test_reference_and_greeting_words_are_not_globally_forbidden(text, name):
    assert extract(text).fields["nombre"] == name


@pytest.mark.parametrize(
    "text,name",
    [
        ("nombre Espejo decorativo", "Espejo decorativo"),
        ("producto Escritorio Boreal", "Escritorio Boreal"),
        ("producto llamadoX Aurora", "llamadoX Aurora"),
    ],
)
def test_introduction_connectors_do_not_consume_name_prefixes(text, name):
    assert_name(extract(text), text, name)


@pytest.mark.parametrize(
    "text",
    [
        "mañana hablamos",
        "estoy grabando",
        "esto funciona bien",
        "todo normal",
        "quizá mañana",
        "nubarrones nubarrones",
    ],
)
def test_sentence_fragments_do_not_supply_a_commercial_noun_phrase(text):
    assert not extract(text).fields


@pytest.mark.parametrize("text", ["Un mueble sin MDF", "Un mueble no MDF"])
def test_negative_material_text_does_not_become_product_name(text):
    result = extract(text)
    assert "nombre" not in result.fields
    assert all(e.decision != "ACCEPTED" for e in result.evidence if e.label == "nombre")
    assert result.unrecognized


@pytest.mark.parametrize(
    "text,name",
    [
        ("Corrijo el nombre a Armario Boreal", "Armario Boreal"),
        ("El nombre comercial es Armario Boreal de MDF", "Armario Boreal"),
        ("Quiero registrar producto: Espejo Aurora con marco metálico", "Espejo Aurora"),
    ],
)
def test_spoken_corrections_and_feature_boundaries(text, name):
    result = extract(text)
    assert result.fields["nombre"] == name
    evidence = next(e for e in result.evidence if e.label == "nombre" and e.decision == "ACCEPTED")
    assert evidence.text == name == text[evidence.start : evidence.end]
