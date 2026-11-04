"""Run the pinned backend's pure structural validator without importing Django.

Only function ASTs and limit constants are loaded from Git blobs. The exception
class is locally substituted; predicate logic and normalizar are the actual
backend source. This is structural compatibility, not a database/service test.
"""

import argparse
import ast
import json
import re
import subprocess
import unicodedata
from pathlib import Path

from training.canonical_v2.io import digest, dump, read

BACKEND_REVISION = "b2d7ef45a8df7b9616abb417517763fe0859983d"


def check(bundle, backend):
    def blob(path):
        return subprocess.check_output(
            ["git", "-C", str(backend), "show", BACKEND_REVISION + ":" + path]
        ).decode()

    catalog = blob("apps/catalogo/atributos_mueble.py")
    validator = blob("apps/proformas/validacion_tecnica.py")
    space = {
        "ValidationError": ValueError,
        "re": re,
        "unicodedata": unicodedata,
        "MAX_COMPONENTES": 40,
        "MAX_CONJUNTOS": 10,
    }
    for source, names in [
        (catalog, {"normalizar"}),
        (validator, {"_texto", "_atributos", "validar_datos_tecnicos"}),
    ]:
        tree = ast.parse(source)
        module = ast.Module(
            body=[
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name in names
            ],
            type_ignores=[],
        )
        exec(compile(module, "pinned-backend-pure-validator", "exec"), space)
    # Check pinned constants rather than rely on locally duplicated limits.
    for node in ast.parse(catalog).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in {"MAX_COMPONENTES", "MAX_CONJUNTOS"}
            for t in node.targets
        ):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "backend-limits", "exec"), space)
    count = 0
    for row in read(bundle / "expected.jsonl"):
        space["validar_datos_tecnicos"](row["expected"]["especificacion"]["datos_tecnicos"])
        count += 1
    return {
        "valid": True,
        "references": count,
        "backend_revision": BACKEND_REVISION,
        "validator_sha256": digest(validator),
        "catalogue_normalizer_sha256": digest(catalog),
        "scope": "PURE_STRUCTURAL_FUNCTIONS_FROM_GIT; local exception class, no database or running services",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--backend", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    report = check(a.bundle, a.backend)
    dump(a.report, report)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
