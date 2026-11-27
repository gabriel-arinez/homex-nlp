"""A singular drawer supplies the same generic furniture detail as a plural."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


@pytest.mark.parametrize(
    "part", ["un cajón", "un cajon", "dos cajones", "una gaveta", "dos gavetas"]
)
def test_generic_furniture_accepts_drawer_detail(part):
    text = f"Un mueble. Con {part}."
    r = RulesEngine().extract(
        ExtractionRequest(request_id="generic-detail", text=text, currency_context="BOB")
    )
    assert r.item_proposal is not None
    assert r.item_proposal.quantity == 1
    assert len(r.item_proposal.components) == 1
    assert all(c.text == text[c.start : c.end] for c in r.candidates)
