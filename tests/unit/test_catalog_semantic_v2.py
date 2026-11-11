"""Catalog voice rules preserve original source evidence and category boundaries."""

import pytest

from homex_nlp.catalog import CatalogRequest, extract_catalog


def extract(text, category="SILLA"):
    result = extract_catalog(CatalogRequest(category=category, text=text))
    assert all(item.text == text[item.start : item.end] for item in result.evidence)
    return result


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Poltrona de sala de espera de estructura y patas de madera maciza",
            "Poltrona de sala de espera",
        ),
        ("Piso flotante de aglomerado HDF de ocho milímetros", "Piso flotante"),
        ("Mesa de reuniones de 120 centímetros", "Mesa de reuniones"),
        ("Zócalo de ochenta milímetros de alto", "Zócalo"),
        ("2 poltronas de estructura metálica", "2 poltronas"),
    ],
)
def test_implicit_name_stops_before_technical_clause(text, expected):
    result = extract(text, "OTRO")
    assert result.fields["nombre"] == expected
    assert result.fields["observaciones"] == text
    assert (
        next(c for c in result.evidence if c.label == "nombre").reason
        == "Nombre delimitado antes de especificaciones técnicas o comerciales"
    )
    assert "cantidad" not in result.fields
    assert "stock" not in result.fields


def test_explicit_name_is_authoritative():
    assert (
        extract("nombre: Mesa de madera para sala de espera").fields["nombre"]
        == "Mesa de madera para sala de espera"
    )


@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        ("be zeta guion doscientos treinta y siete", "BZ-237"),
        ("ene efe guion ochocientos diez", "NF-810"),
        ("ene a nueve uno uno ocho", "NA9118"),
        ("ene efe guion cinco mil doce hache", "NF-5012H"),
        ("equis te guión cero siete dos", "XT-072"),
        ("jota ka guion setecientos cuarenta y dos", "JK-742"),
        ("be de guion cuarenta y uno", "BD-41"),
    ],
)
@pytest.mark.parametrize("category", ["SILLA", "PISO_FLOTANTE"])
def test_spoken_models_have_exact_source_and_interpretation(spoken, expected, category):
    result = extract(f"modelo {spoken}; color azul", category)
    assert result.fields["modelo"] == expected
    candidate = next(item for item in result.evidence if item.label == "modelo")
    assert candidate.text == spoken
    assert candidate.reason == "Equivalencia de código alfanumérico deletreado"


@pytest.mark.parametrize(
    "spoken",
    [
        "be zeta",
        "be zeta guion",
        "be zeta guion doscientos treinta y",
        "be zeta guion dos desconocido",
        "doscientos treinta y siete",
        "be zeta uno o dos",
        "be zeta uno desconocido",
    ],
)
def test_incomplete_or_ambiguous_model_is_not_prefix(spoken):
    assert "modelo" not in extract(f"modelo {spoken}").fields


def test_model_conflicts_negation_correction_and_other_contract():
    assert "modelo" not in extract("modelo jota ka uno o modelo jota ka dos").fields
    assert "modelo" not in extract("no modelo jota ka uno").fields
    assert extract("modelo jota ka uno, mejor modelo jota ka dos").fields["modelo"] == "JK2"
    result = extract("Poltrona modelo jota ka uno de madera", "OTRO")
    assert "modelo" not in result.fields
    assert "especificaciones" not in result.fields


@pytest.mark.parametrize("literal", ["B15b", "XT-742", "Q901", "BE"])
def test_literal_models_unchanged(literal):
    assert extract(f"modelo: {literal}").fields["modelo"] == literal


def test_spoken_code_requires_explicit_model_cue():
    assert "modelo" not in extract("jota ka guion setecientos cuarenta y dos").fields


@pytest.mark.parametrize("phrase", ["de 43", "de cuarenta y tres", "a nueve"])
def test_preposition_or_initial_letter_is_ambiguous_without_spelling_evidence(phrase):
    result = extract(f"modelo {phrase}; color negro")
    assert "modelo" not in result.fields
    evidence = next(c for c in result.evidence if c.label == "modelo")
    assert evidence.decision == "UNRESOLVED"
    assert evidence.text == phrase


@pytest.mark.parametrize("gauge", ["HDF8 milímetros", "HDF ocho mm"])
def test_explicit_hdf_gauge_without_preposition_is_thickness_not_a_model(gauge):
    result = extract(f"Piso flotante de aglomerado {gauge}", "PISO_FLOTANTE")
    assert result.fields["espesor_mm"] == "8"
    assert "espesor_mm" not in extract(f"Piso {gauge} de ancho", "PISO_FLOTANTE").fields
