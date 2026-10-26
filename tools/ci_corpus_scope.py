"""Classify corpus-only versus mixed/production changes; fail closed on uncertainty."""

import argparse
import json
import subprocess
from pathlib import Path


def corpus_only(paths):
    allowed_prefixes = ("data/candidates/corpus_v2_rc2/", "training/corpus_v2_rc2/")
    allowed_files = {
        "tests/training/test_corpus_v2_rc2.py",
        "tools/ci_corpus_scope.py",
        ".github/workflows/corpus-v2-rc2.yml",
        ".github/workflows/ci.yml",
    }
    return bool(paths) and all(p.startswith(allowed_prefixes) or p in allowed_files for p in paths)


def changed_paths(event, head="HEAD"):
    if "pull_request" in event:
        base = event["pull_request"]["base"]["sha"]
    else:
        base = event.get("before", "")
        if not base or not base.strip("0"):
            # A new branch's parent is sufficient only for a single, direct rc2 commit.
            base = subprocess.check_output(["git", "rev-parse", head + "^"], text=True).strip()
            if base != "0154ecba0a53d1a7f3cca4ef10a6cf78cc2ef317":
                return ["__UNKNOWN_NEW_BRANCH_RANGE_REQUIRES_HISTORICAL_CI__"]
    return subprocess.check_output(
        ["git", "diff", "--name-only", base, head], text=True
    ).splitlines()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--event", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        paths = changed_paths(json.loads(a.event.read_text()))
        only = corpus_only(paths)
    except (ValueError, KeyError, subprocess.CalledProcessError):
        paths = []
        only = False
    with a.output.open("a") as f:
        f.write("corpus_only=" + str(only).lower() + "\n")
    print(
        json.dumps(
            {
                "corpus_only": only,
                "changed_paths": paths,
                "policy": "production/mixed/unknown preserves historical jobs; corpus-only skips package/training, security jobs remain",
            }
        )
    )


if __name__ == "__main__":
    main()
