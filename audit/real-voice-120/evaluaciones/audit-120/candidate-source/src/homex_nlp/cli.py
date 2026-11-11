"""CLI local de texto para F03; stdout contiene exclusivamente JSON del contrato."""

from __future__ import annotations

import argparse
import json
import sys

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="homex-nlp")
    parser.add_argument("text", nargs="?", help="Texto dictado; si falta se lee stdin completo.")
    parser.add_argument("--request-id", default="local-cli")
    parser.add_argument("--currency", choices=("BOB", "USD"), default="BOB")
    arguments = parser.parse_args(argv)
    text = arguments.text if arguments.text is not None else sys.stdin.read()
    request = ExtractionRequest(
        request_id=arguments.request_id,
        text=text,
        currency_context=arguments.currency,
    )
    result = RulesEngine().extract(request)
    json.dump(result.model_dump(mode="json"), sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
