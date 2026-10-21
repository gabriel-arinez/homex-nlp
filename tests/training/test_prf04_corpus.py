import json
from pathlib import Path

from training.audit_prf04 import FAMILIAS, auditar


def test_cuatro_fuentes_autorizadas_sin_fuga_y_expected_completo():
    reporte = auditar()
    assert not reporte["errores_formales"]
    assert sum(f["registros"] for f in reporte["fuentes"].values()) == 675
    for familia in FAMILIAS:
        source = [
            json.loads(line)
            for line in Path(f"data/corpus/{familia}.jsonl").read_text().splitlines()
        ]
        targets = [
            json.loads(line)
            for line in Path(f"data/expected/{familia}.jsonl").read_text().splitlines()
        ]
        assert {r["id"]: r["text_sha256"] for r in source} == {
            r["id"]: r["text_sha256"] for r in targets
        }
        assert all(r["metadata"]["fuente_autorizada_prf04"] for r in source)
        assert all("expected" in r and "comercial" in r["expected"] for r in targets)
