"""Public catalog regressions for complete spelling versus ordinary model prose."""

import pytest

from homex_nlp.catalog import CatalogRequest, extract_catalog


def extract(text, category):
    result = extract_catalog(CatalogRequest(category=category, text=text))
    assert all(item.text == text[item.start : item.end] for item in result.evidence)
    return result


@pytest.mark.parametrize("category", ["SILLA", "PISO_FLOTANTE"])
@pytest.mark.parametrize("phrase", ["Modelo B O dos", "Código B O 2", "Modelo be o dos"])
def test_complete_spelling_accepts_letter_o_before_number(category, phrase):
    text = "Descripción: prueba; " + phrase
    result = extract(text, category)
    assert result.fields["modelo"] == "BO2"
    candidate = next(item for item in result.evidence if item.label == "modelo")
    assert candidate.text in {"B O dos", "B O 2", "be o dos"}
    assert candidate.decision == "ACCEPTED"
    assert candidate.reason == "Equivalencia de código alfanumérico deletreado"
    assert not any(warning.startswith("modelo:") for warning in result.warnings)


@pytest.mark.parametrize("category", ["SILLA", "PISO_FLOTANTE"])
@pytest.mark.parametrize("phrase", ["modelo a medida", "modelo de madera", "modelo de"])
def test_ordinary_prepositions_are_not_ambiguous_codes(category, phrase):
    result = extract(phrase, category)
    assert "modelo" not in result.fields
    assert not any(item.label == "modelo" for item in result.evidence)
    assert not any(warning.startswith("modelo:") for warning in result.warnings)


@pytest.mark.parametrize("category", ["SILLA", "PISO_FLOTANTE"])
@pytest.mark.parametrize(
    "phrase",
    [
        "Modelo B o modelo C",
        "Modelo B, o mejor C",
        "Modelo be zeta uno o dos",
        "modelo be zeta",
        "modelo be zeta guion",
        "modelo de 43",
        "modelo a nueve",
    ],
)
def test_alternatives_and_incomplete_spelling_remain_unresolved(category, phrase):
    result = extract(phrase, category)
    assert "modelo" not in result.fields
    candidates = [item for item in result.evidence if item.label == "modelo"]
    assert candidates and all(item.decision == "UNRESOLVED" for item in candidates)
    assert any(warning.startswith("modelo:") for warning in result.warnings)


@pytest.mark.parametrize("category", ["SILLA", "PISO_FLOTANTE"])
@pytest.mark.parametrize(
    ("phrase", "expected"),
    [
        ("modelo B15b", "B15b"),
        ("modelo A1", "A1"),
        ("modelo D2", "D2"),
        ("modelo XT-072", "XT-072"),
        ("modelo be de guion cuarenta y uno", "BD-41"),
        ("modelo ene efe guion cinco mil doce hache", "NF-5012H"),
    ],
)
def test_existing_literal_and_spoken_models_are_preserved(category, phrase, expected):
    assert extract(phrase, category).fields["modelo"] == expected


@pytest.mark.parametrize("phrase", ["Modelo B O dos", "modelo de madera", "modelo B15b"])
def test_other_category_does_not_acquire_model_support(phrase):
    result = extract(phrase, "OTRO")
    assert "modelo" not in result.fields
    assert not any(item.label == "modelo" for item in result.evidence)
