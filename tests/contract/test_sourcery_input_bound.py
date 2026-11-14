"""Extraction rejects oversized text without rewriting source evidence."""

import pytest
from pydantic import ValidationError

from homex_nlp.contracts import ExtractionRequest


def test_extraction_text_bound_rejects_instead_of_truncating():
    text = "x" * 20_000
    assert ExtractionRequest(request_id="bound", text=text, currency_context="BOB").text == text
    with pytest.raises(ValidationError, match="20000"):
        ExtractionRequest(request_id="bound", text=text + "x", currency_context="BOB")


def test_request_schema_declares_the_same_bound():
    assert ExtractionRequest.model_json_schema()["properties"]["text"]["maxLength"] == 20_000
