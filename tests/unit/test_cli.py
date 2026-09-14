import json

from homex_nlp.cli import main


def test_cli_emits_one_contract_json(capsys) -> None:
    assert main(["--request-id", "cli-1", "dos escritorios, total 2000"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["request_id"] == "cli-1"
    assert payload["item_proposal"]["price"]["line_total"] == "2000.00"
