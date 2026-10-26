"""Evalúa dictados consentidos sin almacenar audio ni promover modelos automáticamente.

La revisión de dominio y la representatividad se acreditan externamente;
este script comprueba la presencia de metadatos y calcula métricas descriptivas.
"""

import argparse
import json
import re
from pathlib import Path
from statistics import median


def palabras(texto):
    return re.findall(r"\w+", texto.casefold(), flags=re.UNICODE)


def distancia(referencia, hipotesis):
    previo = list(range(len(hipotesis) + 1))
    for i, palabra in enumerate(referencia, 1):
        actual = [i]
        for j, predicha in enumerate(hipotesis, 1):
            actual.append(min(actual[-1] + 1, previo[j] + 1, previo[j - 1] + (palabra != predicha)))
        previo = actual
    return previo[-1]


def evaluar(fuente):
    registros = [json.loads(linea) for linea in fuente.read_text().splitlines() if linea.strip()]
    if not registros:
        raise ValueError("No hay sesiones autorizadas para evaluar.")
    identificadores = set()
    errores = palabras_totales = 0
    manual, asistido, correcciones = [], [], []
    conteo_estructurado = {"A_RULES_ONLY": 0, "B_NER_ASSEMBLER": 0, "C_HYBRID_EXPERIMENTAL": 0}
    casos_estructurados = 0
    for registro in registros:
        identificador = registro.get("id_sesion")
        if (
            not isinstance(identificador, str)
            or not identificador
            or identificador in identificadores
        ):
            raise ValueError("Cada sesión requiere un ID anónimo único.")
        identificadores.add(identificador)
        if registro.get("autorizada") is not True or registro.get("fuente") != "DICTADO_VENDEDOR":
            raise ValueError("No usar sesiones sintéticas o sin autorización.")
        if not isinstance(registro.get("revisor_dominio"), str) or not registro["revisor_dominio"]:
            raise ValueError("Falta identificación del revisor de dominio.")
        referencia = registro.get("transcripcion_referencia")
        hipotesis = registro.get("transcripcion_asr")
        if not isinstance(referencia, str) or not isinstance(hipotesis, str):
            raise ValueError("Faltan transcripciones de referencia y ASR.")
        tokens = palabras(referencia)
        if not tokens:
            raise ValueError("La transcripción de referencia no puede estar vacía.")
        errores += distancia(tokens, palabras(hipotesis))
        palabras_totales += len(tokens)
        for campo, destino in (
            ("tiempo_manual_seg", manual),
            ("tiempo_asistido_seg", asistido),
        ):
            valor = registro.get(campo)
            if type(valor) not in (int, float) or not 0 < valor < float("inf"):
                raise ValueError(f"Tiempo inválido: {campo}.")
            destino.append(valor)
        numero = registro.get("correcciones")
        if type(numero) is not int or numero < 0:
            raise ValueError("Correcciones no negativas obligatorias.")
        correcciones.append(numero)
        referencia_estructurada = registro.get("estructura_referencia")
        variantes = registro.get("variantes")
        if (referencia_estructurada is None) != (variantes is None):
            raise ValueError("Las referencias estructuradas y las variantes deben venir juntas.")
        if referencia_estructurada is not None:
            if not isinstance(referencia_estructurada, dict) or not isinstance(variantes, dict):
                raise ValueError("Las referencias y las variantes deben ser objetos.")
            if set(variantes) != set(conteo_estructurado):
                raise ValueError("Se requieren A, B y C para comparación imparcial.")
            casos_estructurados += 1
            for nombre, salida in variantes.items():
                conteo_estructurado[nombre] += salida == referencia_estructurada
    return {
        "procedencia": "SESIONES_DECLARADAS_AUTORIZADAS_CON_REVISION_IDENTIFICADA",
        "certificacion_independiente": False,
        "promover_modelo": False,
        "sesiones": len(registros),
        "wer_micro": errores / palabras_totales,
        "errores_transcripcion": errores,
        "palabras_referencia": palabras_totales,
        "mediana_manual_seg": median(manual),
        "mediana_asistido_seg": median(asistido),
        "mediana_ahorro_seg": median([a - b for a, b in zip(manual, asistido)]),
        "total_correcciones": sum(correcciones),
        "comparacion_estructurada": {
            "casos": casos_estructurados,
            "json_exacto": conteo_estructurado if casos_estructurados else None,
        },
        "nota": "No acredita consentimiento, independencia, representatividad ni umbrales.",
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in {
        "validate",
        "prepare-review",
        "score",
        "aggregate",
        "schema",
    }:
        from training.benchmark_campo.cli import main

        raise SystemExit(main())
    parser = argparse.ArgumentParser()
    parser.add_argument("sesiones", type=Path, help="JSONL local fuera del repositorio")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    resultado = evaluar(args.sesiones)
    args.output.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    print(f"Evaluadas {resultado['sesiones']} sesiones declaradas; sin promoción automática.")
