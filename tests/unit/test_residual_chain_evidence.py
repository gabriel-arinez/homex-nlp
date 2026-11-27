"""Whole chains and their operands have independent normalized evidence."""

import pytest
from test_residual_dimensions import extract


@pytest.mark.parametrize(
    "text", ["mesa de dos por tres", "Una mesa de 2 por 3 por 1", "Una mesa de 60 por 80"]
)
def test_chain_evidence_not_overwritten(text):
    result = extract(text)
    chain = next(c for c in result.candidates if c.label == "DIMENSION" and "por" in c.text)
    assert isinstance(chain.normalized_value, dict)
    assert len(chain.normalized_value["operands"]) == len(result.item_proposal.dimensions)
    for d in result.item_proposal.dimensions:
        operand = next(
            c
            for c in result.candidates
            if c.candidate_id in d.evidence_ids and c.candidate_id != chain.candidate_id
        )
        assert d.axis is None
        if isinstance(operand.normalized_value, dict):
            assert operand.normalized_value["value"] == d.value
        else:
            assert operand.normalized_value[0] == d.value
