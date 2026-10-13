import json
from pathlib import Path


def test_ap6_adapter_preserves_v1_and_requires_human_unit_price() -> None:
    evidence = json.loads(
        (Path(__file__).parents[2] / "docs" / "ap6-commercial-adapter-v2.json").read_text()
    )

    assert evidence["adapter_version"] == "2.0"
    assert evidence["nlp_package"] == "homex-nlp==0.1.0"
    assert evidence["nlp_schema_version"] == "1.0"
    assert evidence["nlp_mode"] == "RULES_ONLY"
    assert evidence["policy"] == {
        "nlp_is_commercial_authority": False,
        "nlp_total_is_copied_to_unit_price": False,
        "new_line_mode": "PRECIO_UNITARIO",
        "seller_must_confirm_unit_price": True,
        "catalog_import_from_ner": False,
        "approved_quote_automatically": False,
    }
    assert evidence["compatibility"]["public_contract_v1_changed"] is False
    assert evidence["compatibility"]["legacy_total_negotiated_evidence_preserved"] is True
