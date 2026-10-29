"""Read frozen private inputs; evaluate RULES_ONLY using the unchanged decision protocol.

References, splits and denominators belong to the input. Never generates gold.
"""

import argparse
import json
from pathlib import Path

from training.decision_nlp import evaluate_rows, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.inputs.read_text().splitlines()]
    outputs = evaluate_rows(rows, "M-A")
    report = {
        "rows": outputs,
        "subsets": {
            subset: metrics([r for r in outputs if r["subset"] == subset])
            for subset in sorted({r["subset"] for r in outputs})
        },
    }
    with args.output.open("x") as target:
        json.dump(report, target, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
