import json

import pytest

from training.evaluar_campo_prf04 import distancia, evaluar, palabras


def sesion(**cambios):
    registro = {
        "id_sesion": "VENDEDOR-ANON-01",
        "autorizada": True,
        "fuente": "DICTADO_VENDEDOR",
        "revisor_dominio": "REV-ANON-01",
        "transcripcion_referencia": "Un escritorio con dos cajones",
        "transcripcion_asr": "Un escritorio con tres cajones",
        "tiempo_manual_seg": 120,
        "tiempo_asistido_seg": 70,
        "correcciones": 1,
    }
    return registro | cambios


def cargar(tmp_path, *registros):
    archivo = tmp_path / "sesiones-autorizadas-prueba.jsonl"
    archivo.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in registros))
    return archivo


def test_distancia_wer_separa_sustituciones_y_no_infiere_calidad():
    assert palabras("DOS cajones") == ["dos", "cajones"]
    assert distancia(palabras("dos cajones"), palabras("tres cajones")) == 1


def test_evaluacion_calcula_wer_y_productividad_sin_promover(tmp_path):
    reporte = evaluar(cargar(tmp_path, sesion()))
    assert reporte["sesiones"] == 1
    assert reporte["wer_micro"] == 1 / 5
    assert reporte["mediana_ahorro_seg"] == 50
    assert reporte["total_correcciones"] == 1
    assert reporte["comparacion_estructurada"]["json_exacto"] is None
    assert reporte["promover_modelo"] is False
    assert reporte["certificacion_independiente"] is False


@pytest.mark.parametrize(
    "cambios",
    [
        {"autorizada": False},
        {"fuente": "SINTETICO"},
        {"revisor_dominio": ""},
        {"transcripcion_referencia": ""},
        {"tiempo_manual_seg": -1},
        {"correcciones": -1},
        {"estructura_referencia": {}},
    ],
)
def test_gates_impiden_aceptar_entradas_sin_control(tmp_path, cambios):
    with pytest.raises(ValueError):
        evaluar(cargar(tmp_path, sesion(**cambios)))


def test_referencias_de_dominio_comparan_las_tres_variantes(tmp_path):
    r = sesion(
        estructura_referencia={"comercial": {"cantidad": 2}},
        variantes={
            "A_RULES_ONLY": {"comercial": {"cantidad": 1}},
            "B_NER_ASSEMBLER": {"comercial": {"cantidad": 2}},
            "C_HYBRID_EXPERIMENTAL": {"comercial": {"cantidad": 2}},
        },
    )
    reporte = evaluar(cargar(tmp_path, r))
    assert reporte["comparacion_estructurada"] == {
        "casos": 1,
        "json_exacto": {
            "A_RULES_ONLY": 0,
            "B_NER_ASSEMBLER": 1,
            "C_HYBRID_EXPERIMENTAL": 1,
        },
    }
