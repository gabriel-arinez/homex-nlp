"""Independent commercial relation probes; no corpus identifiers or customer data."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="commercial-relation-probe", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize("product,quantity", [("estante librero", 1), ("estantes libreros", 3)])
def test_compound_shelving_name_is_one_product(product, quantity):
    result = extract(f"{quantity} {product} de 95 cm de ancho. Precio unitario 780 bolivianos.")
    assert result.status == "REQUIRES_REVIEW"
    assert result.proposed_item_count == 1
    assert result.item_proposal.name.lower() == product
    assert result.item_proposal.quantity == quantity
    assert result.item_proposal.price.stated_amount == "780.00"
    assert any(d.axis == "ancho" and d.value_mm == "950" for d in result.item_proposal.dimensions)
    assert not any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)
    assert (
        len([c for c in result.candidates if c.label == "PRODUCTO" and c.decision == "ACCEPTED"])
        == 1
    )


@pytest.mark.parametrize(
    "text",
    [
        "Un estante y un librero.",
        "Un estante o librero.",
        "Dos estantes. Tres libreros de 95 cm de ancho.",
        "Un estante librero y otro librero.",
        "Un juego de mesas. Dos mesas de diferentes tamaños.",
        "Una mesa. Una mesa de 95 cm de ancho.",
        "Un escritorio. Credenza lateral derecha de 95 cm de ancho.",
        "Un casillero de seis puertas. Seis casilleros con cerradura.",
    ],
)
def test_independent_alternative_and_unresolved_compositions_still_abstain(text):
    result = extract(text)
    assert result.status == "NO_PROPOSAL"
    assert result.item_proposal is None
    assert result.proposed_item_count == 0
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)


@pytest.mark.parametrize("introduction", ["cajonera", "cajonería"])
@pytest.mark.parametrize(
    "reference", ["Cajonera rodante de 35 cm de ancho", "Incluye cajonera rodante"]
)
def test_introduced_drawer_references_do_not_create_an_order(introduction, reference):
    result = extract(
        f"Dos escritorios con {introduction} rodante. Escritorio de 125 cm de ancho. "
        f"{reference}. Precio unitario 1900 bolivianos."
    )
    assert result.status == "REQUIRES_REVIEW"
    assert result.item_proposal.quantity == 2
    assert result.item_proposal.price.stated_amount == "1900.00"
    drawers = [
        c for c in result.item_proposal.components if c.name.casefold() in {"cajonera", "cajonería"}
    ]
    assert len(drawers) == 1
    if reference.startswith("Cajonera"):
        dimension = next(d for d in result.item_proposal.dimensions if d.value_mm == "350")
        assert dimension.component_ref == drawers[0].component_id
    assert any(
        d.value_mm == "1250" and d.component_ref is None for d in result.item_proposal.dimensions
    )
    assert any(c.label == "PRODUCTO" and c.decision == "REJECTED" for c in result.candidates)


def test_explicit_integrated_credenza_keeps_its_own_measures_and_material():
    result = extract(
        "Dos escritorios de 125 cm de ancho y 75 cm de alto. "
        "Credenza integrada de MDF de 105 cm de ancho, 60 cm de alto y 45 cm de profundidad. "
        "Precio unitario 2100 bolivianos."
    )
    assert result.status == "REQUIRES_REVIEW"
    assert result.item_proposal.quantity == 2
    assert result.item_proposal.price.stated_amount == "2100.00"
    component = next(
        c for c in result.item_proposal.components if c.name.lower() == "credenza integrada"
    )
    dims = result.item_proposal.dimensions
    assert {(d.axis, d.value_mm) for d in dims if d.component_ref == component.component_id} == {
        ("ancho", "1050"),
        ("alto", "600"),
        ("profundidad", "450"),
    }
    assert {(d.axis, d.value_mm) for d in dims if d.component_ref is None} == {
        ("ancho", "1250"),
        ("alto", "750"),
    }
    assert (
        next(
            c for c in result.candidates if c.label == "MATERIAL" and c.text == "MDF"
        ).component_ref
        == component.component_id
    )


@pytest.mark.parametrize(
    "text",
    [
        "Un escritorio y una cajonera rodante de 35 cm de ancho.",
        "Un escritorio con cajonera. Otra cajonera rodante de 35 cm de ancho.",
        "Un escritorio con cajonería. Dos cajoneras rodantes de 35 cm de ancho.",
        "Un escritorio y una credenza integrada de 105 cm de ancho.",
        "Un escritorio. Credenza de 105 cm de ancho.",
        "Un escritorio con cajonera. Incluye otra cajonera rodante.",
    ],
)
def test_drawer_and_credenza_independence_is_preserved(text):
    result = extract(text)
    assert result.status == "NO_PROPOSAL"
    assert result.item_proposal is None
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)


@pytest.mark.parametrize("quantity", [2, 4])
def test_literal_credencia_with_explicit_furniture_context(quantity):
    result = extract(
        f"{quantity} credencias de 105 cm de ancho, cuerpo de melamina. Precio unitario 850 bolivianos."
    )
    assert result.status == "REQUIRES_REVIEW"
    assert result.item_proposal.name == "credencias"
    assert result.item_proposal.quantity == quantity
    assert result.item_proposal.price.stated_amount == "850.00"
    assert any(d.axis == "ancho" and d.value_mm == "1050" for d in result.item_proposal.dimensions)
    assert not any(w.code == "NO_PRODUCT" for w in result.warnings)


@pytest.mark.parametrize(
    "text", ["Dos credencias.", "Una trill de 65 cm de ancho.", "Credenciales de melamina."]
)
def test_unsupported_or_ambiguous_lexemes_are_not_repaired(text):
    result = extract(text)
    assert result.status == "NO_PROPOSAL"
    assert result.item_proposal is None
    assert any(w.code == "NO_PRODUCT" for w in result.warnings)


def test_includes_does_not_merge_an_unintroduced_main_product():
    result = extract("Una mesa. Incluye mesa de 95 cm de ancho.")
    assert result.status == "NO_PROPOSAL"
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)


def test_credencia_needs_an_explicit_dimension_not_just_a_number():
    result = extract("Dos credencias de cinco ideas, madera de ejemplo.")
    assert result.status == "NO_PROPOSAL"
    assert any(w.code == "NO_PRODUCT" for w in result.warnings)


@pytest.mark.parametrize("product", ["estante", "librero", "credenza"])
def test_existing_standalone_furniture_remains_a_single_order(product):
    result = extract(f"Dos {product}s de 95 cm de ancho. Precio unitario 780 bolivianos.")
    assert result.status == "REQUIRES_REVIEW"
    assert result.item_proposal.quantity == 2
    assert result.item_proposal.price.stated_amount == "780.00"


def test_reference_dimension_scope_stops_at_a_new_clause():
    result = extract(
        "Un escritorio con cajonera rodante. Cajonera rodante de 35 cm de ancho y 55 cm de alto. "
        "Escritorio de 125 cm de ancho. Precio unitario 1900 bolivianos."
    )
    assert result.status == "REQUIRES_REVIEW"
    drawer = next(c.component_id for c in result.item_proposal.components if c.name == "cajonera")
    assert {
        (d.axis, d.value_mm) for d in result.item_proposal.dimensions if d.component_ref == drawer
    } == {("ancho", "350"), ("alto", "550")}
    assert any(
        d.value_mm == "1250" and d.component_ref is None for d in result.item_proposal.dimensions
    )
