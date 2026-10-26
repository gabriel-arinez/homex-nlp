"""Explicit reconstruction of the complete candidate, including deterministic reports."""

import argparse
from pathlib import Path

from training.corpus_v2.build import DEFAULT, build
from training.corpus_v2.report import report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    build(out=args.output)
    report(args.output)


if __name__ == "__main__":
    main()
