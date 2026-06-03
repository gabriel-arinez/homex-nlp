"""
convert_to_spacy.py — Conversión de anotaciones JSONL a corpus spaCy v3
=======================================================================
Convierte el JSONL exportado de Doccano (o anotado manualmente) al formato
binario .spacy que requiere el entrenador de spaCy.

Flujo:
  pedidos_reales_anotados.jsonl
    → validar offsets
    → filtrar ejemplos inválidos con log
    → split 80/20 train/dev
    → train.spacy + dev.spacy

Uso:
  python convert_to_spacy.py

Requisitos:
  pip install spacy
  python -m spacy download es_core_news_sm
"""

import json
import random
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

import spacy
from spacy.tokens import DocBin
from spacy.training import Example

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("homex.convert")

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
JSONL_PATH   = Path("../data/doccano_exports/pedidos_reales_anotados.jsonl")
OUTPUT_DIR   = Path("../data/spacy_corpus")
SPLIT_RATIO  = 0.8   # 80% entrenamiento, 20% desarrollo
RANDOM_SEED  = 42

# Etiquetas esperadas — deben coincidir exactamente con las usadas al anotar
LABELS_VALIDOS = {
    "PRODUCTO", "MATERIAL", "ESPESOR", "COLOR",
    "DIMENSION", "CANTIDAD", "ACCESORIO", "PRECIO", "ACABADO"
}

# =============================================================================
# CARGA Y VALIDACIÓN
# =============================================================================

def cargar_jsonl(ruta: Path) -> List[Dict[str, Any]]:
    """Carga todos los registros del JSONL línea por línea."""
    registros = []
    with open(ruta, encoding="utf-8") as f:
        for i, linea in enumerate(f, 1):
            linea = linea.strip()
            if not linea:
                continue
            try:
                registros.append(json.loads(linea))
            except json.JSONDecodeError as e:
                logger.warning(f"[Línea {i}] JSON inválido, ignorando: {e}")
    logger.info(f"Cargados {len(registros)} registros desde {ruta}")
    return registros


def validar_entidades(texto: str, entidades: List[Tuple]) -> Tuple[List[Tuple], List[str]]:
    """
    Valida que los offsets de cada entidad sean correctos:
    1. start < end
    2. start y end dentro de los límites del texto
    3. El span no empieza ni termina en medio de un carácter (UTF-8)
    4. La etiqueta está en LABELS_VALIDOS

    Retorna: (entidades_validas, lista_de_advertencias)
    """
    validas = []
    advertencias = []

    for (start, end, label) in entidades:
        # Verificar límites
        if start < 0 or end > len(texto) or start >= end:
            advertencias.append(
                f"Offset inválido [{start}:{end}] para '{label}' en texto de {len(texto)} chars"
            )
            continue

        # Verificar que el span tenga contenido
        span_texto = texto[start:end]
        if not span_texto.strip():
            advertencias.append(f"Span vacío [{start}:{end}] para '{label}'")
            continue

        # Verificar etiqueta
        if label not in LABELS_VALIDOS:
            advertencias.append(
                f"Etiqueta desconocida '{label}' en [{start}:{end}]. "
                f"Etiquetas válidas: {LABELS_VALIDOS}"
            )
            continue

        validas.append((start, end, label))

    return validas, advertencias


def registros_a_ejemplos_spacy(
    registros: List[Dict],
    nlp
) -> List[Example]:
    """
    Convierte registros JSONL a objetos Example de spaCy.
    Usa 'entities' en formato [(start, end, label), ...].
    Los registros con errores de alineación se omiten con log de advertencia.
    """
    ejemplos = []
    omitidos = 0

    for reg in registros:
        texto = reg.get("text", "")
        entidades_raw = reg.get("entities", [])

        # Normalizar a tuplas (start, end, label)
        entidades = [(int(s), int(e), l) for s, e, l in entidades_raw]

        # Validar offsets
        entidades_validas, advertencias = validar_entidades(texto, entidades)
        for adv in advertencias:
            logger.warning(f"[ID {reg.get('id', '?')}] {adv}")

        if not texto:
            logger.warning(f"[ID {reg.get('id', '?')}] Texto vacío, ignorando.")
            omitidos += 1
            continue

        # Crear Doc y Example
        doc = nlp.make_doc(texto)
        anotaciones = {"entities": entidades_validas}

        try:
            ejemplo = Example.from_dict(doc, anotaciones)
            ejemplos.append(ejemplo)
        except Exception as e:
            logger.warning(
                f"[ID {reg.get('id', '?')}] Error al crear Example (posible "
                f"desalineación de tokens): {e}. Ignorando."
            )
            omitidos += 1

    logger.info(
        f"Ejemplos válidos: {len(ejemplos)} | Omitidos: {omitidos}"
    )
    return ejemplos


def guardar_docbin(ejemplos: List[Example], ruta: Path) -> None:
    """Guarda una lista de Examples en un archivo .spacy binario."""
    db = DocBin()
    for ejemplo in ejemplos:
        db.add(ejemplo.reference)
    db.to_disk(ruta)
    logger.info(f"Guardado: {ruta} ({len(ejemplos)} ejemplos)")


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar modelo base (solo para tokenización)
    try:
        nlp = spacy.load("es_core_news_sm", exclude=["ner", "parser", "tagger"])
    except OSError:
        logger.warning("es_core_news_sm no encontrado. Usando modelo en blanco.")
        nlp = spacy.blank("es")

    # Cargar registros
    registros = cargar_jsonl(JSONL_PATH)
    if not registros:
        logger.error("No se cargaron registros. Verificar el JSONL.")
        return

    # Convertir a Examples
    ejemplos = registros_a_ejemplos_spacy(registros, nlp)
    if not ejemplos:
        logger.error("No se generaron ejemplos válidos. Verificar offsets en el JSONL.")
        return

    # Split train/dev
    random.seed(RANDOM_SEED)
    random.shuffle(ejemplos)
    corte = int(len(ejemplos) * SPLIT_RATIO)
    train_ejemplos = ejemplos[:corte]
    dev_ejemplos   = ejemplos[corte:]

    # Asegurar al menos 1 ejemplo en dev
    if not dev_ejemplos and len(train_ejemplos) > 1:
        dev_ejemplos = [train_ejemplos.pop()]

    logger.info(f"Split: {len(train_ejemplos)} train / {len(dev_ejemplos)} dev")

    # Guardar corpus binario
    guardar_docbin(train_ejemplos, OUTPUT_DIR / "train.spacy")
    guardar_docbin(dev_ejemplos,   OUTPUT_DIR / "dev.spacy")

    # Resumen de labels presentes en el corpus
    labels_en_corpus = set()
    for ej in ejemplos:
        for ent in ej.reference.ents:
            labels_en_corpus.add(ent.label_)

    logger.info(f"Labels en el corpus: {sorted(labels_en_corpus)}")
    labels_faltantes = LABELS_VALIDOS - labels_en_corpus
    if labels_faltantes:
        logger.warning(
            f"Labels definidos pero sin ejemplos en el corpus: {sorted(labels_faltantes)}. "
            f"Agregar al menos 10 ejemplos por label antes de entrenar."
        )

    print("\n✅ Corpus generado:")
    print(f"   train.spacy → {len(train_ejemplos)} ejemplos")
    print(f"   dev.spacy   → {len(dev_ejemplos)} ejemplos")
    print(f"   Labels presentes: {sorted(labels_en_corpus)}")
    print(f"\n➡️  Próximo paso: python -m spacy train config.cfg --output ../data/modelos_entrenados/")


if __name__ == "__main__":
    main()