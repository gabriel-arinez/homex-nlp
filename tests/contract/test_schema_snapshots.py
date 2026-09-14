import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_exported_schemas_are_current() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "export_schemas.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == "Esquemas v1: OK"


def test_schemas_are_draft_2020_12_documents() -> None:
    schemas = sorted((ROOT / "schemas").glob("*.schema.json"))
    assert len(schemas) == 5
    for path in schemas:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"] == f"urn:homex:nlp:schema:{path.stem.removesuffix('.schema')}"
        assert schema["additionalProperties"] is False


def test_normative_examples_validate_against_exported_json_schemas() -> None:
    request_schema = json.loads(
        (ROOT / "schemas" / "extraction-request-v1.schema.json").read_text(encoding="utf-8")
    )
    result_schema = json.loads(
        (ROOT / "schemas" / "extraction-result-v1.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(request_schema)
    jsonschema.Draft202012Validator.check_schema(result_schema)

    for path in sorted((ROOT / "examples" / "requests").glob("*.json")):
        jsonschema.validate(json.loads(path.read_text(encoding="utf-8")), request_schema)
    for path in sorted((ROOT / "examples" / "expected").glob("*.json")):
        jsonschema.validate(json.loads(path.read_text(encoding="utf-8")), result_schema)

    invalid_request = json.loads(
        (ROOT / "examples" / "requests" / "total-negociado.json").read_text(encoding="utf-8")
    )
    invalid_request["currency_context"] = "EUR"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid_request, request_schema)
