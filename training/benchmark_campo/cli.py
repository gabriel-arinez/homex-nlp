"""Offline CLI; outputs private by default and never echoes validation values."""

import argparse
from pathlib import Path

from pydantic import ValidationError

from training.benchmark_campo.models import Batch, Session
from training.benchmark_campo.pipeline import (
    canonical,
    combine,
    digest,
    load,
    read_json,
    review_kit,
    score,
    write_private,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=["validate", "prepare-review", "score", "aggregate", "schema"]
    )
    parser.add_argument("inputs", nargs="*", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--private-detail",
        action="store_true",
        help="Includes all private literals; NEVER publish this output",
    )
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--authorized-reviewers", type=Path)
    parser.add_argument(
        "--previously-open",
        type=Path,
        help="Private JSON list: text/case/source/template/speaker/partition/audio hash",
    )
    args = parser.parse_args(argv)
    try:
        if args.operation == "schema":
            result = {"batch": Batch.model_json_schema(), "session": Session.model_json_schema()}
        else:
            if not args.inputs or (args.operation != "aggregate" and len(args.inputs) != 1):
                raise ValueError("INPUT_COUNT")
            batches = [load(p) for p in args.inputs]
            batch = combine(batches)
            if args.operation == "prepare-review":
                result = review_kit(batch)
            elif args.operation == "validate":
                result = {
                    "valid": True,
                    "sessions": len(batch.sessions),
                    "consent": "human_declared_IS_NOT_human_verified",
                    "human_gold": "NO",
                }
            else:
                if bool(args.decisions) != bool(args.authorized_reviewers):
                    raise ValueError("EXTERNAL_DECISIONS_AND_REGISTRY_REQUIRED_TOGETHER")
                result = score(
                    batch,
                    read_json(args.decisions) if args.decisions else [],
                    read_json(args.authorized_reviewers) if args.authorized_reviewers else [],
                    read_json(args.previously_open) if args.previously_open else [],
                    args.private_detail,
                )
                result["input_digests"] = [digest(b.model_dump(mode="json")) for b in batches]
            if args.private_detail and args.operation not in {"score", "aggregate"}:
                raise ValueError("PRIVATE_DETAIL_REQUIRES_SCORING")
        write_private(args.output, result)
    except (ValueError, ValidationError, OSError, KeyError, TypeError):
        # Pydantic exceptions contain input_value, never expose them in a terminal.
        print(
            canonical(
                {
                    "ok": False,
                    "error": "INVALID_INPUT_OR_PRIVATE_PATH",
                    "detail": "Inspect privately against schema; no input values logged",
                }
            ).strip()
        )
        return 2
    print(canonical({"ok": True, "operation": args.operation, "private_output": True}).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
