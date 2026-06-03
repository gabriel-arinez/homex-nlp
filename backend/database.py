# =============================================================================
# database.py — HOMEX Capa de Persistencia v4.0
# Responsabilidad única: toda interacción con SQLite pasa por este módulo.
# El backend (main.py) NUNCA debe importar sqlite3 directamente.
#
# Esquema de tablas:
#   capturas           → una fila por grabación de voz
#   items_ia           → N filas por captura (un mueble por fila, detectado por IA)
#   items_humano       → N filas por captura (corrección del operador por mueble)
#   metricas_pipeline  → una fila por captura (latencias, precisión HITL)
#
# Esta estructura resuelve el problema de cotizaciones con múltiples muebles
# y permite evaluación académica real: precisión por entidad, tasa de corrección,
# latencia por etapa, análisis de errores frecuentes.
# =============================================================================

import sqlite3
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = "homex_trazabilidad.db"


# =============================================================================
# SECCIÓN 1: INICIALIZACIÓN DEL ESQUEMA
# =============================================================================

def init_db() -> None:
    """
    Crea las tablas si no existen.
    Seguro para llamar múltiples veces (IF NOT EXISTS).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # TABLA: capturas
    # Una fila por grabación/procesamiento.
    # Almacena el texto transcrito y metadata de la sesión.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS capturas (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           DATETIME DEFAULT CURRENT_TIMESTAMP,
            texto_transcrito    TEXT NOT NULL,
            texto_normalizado   TEXT,
            modelo_version      TEXT,
            latencia_total_ms   INTEGER,
            latencia_asr_ms     INTEGER,
            latencia_nlp_ms     INTEGER,
            num_items_ia        INTEGER DEFAULT 0,
            labels_detectados   TEXT,   -- JSON array de etiquetas encontradas
            advertencias_motor  TEXT    -- JSON array de advertencias del NLP engine
        )
    """)

    # ------------------------------------------------------------------
    # TABLA: items_ia
    # Un registro por mueble detectado por la IA en una captura.
    # Permite cotizaciones con N muebles sin perder información.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_ia (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            captura_id      INTEGER NOT NULL REFERENCES capturas(id),
            orden           INTEGER NOT NULL,  -- posición del mueble (0, 1, 2...)
            producto        TEXT,
            material        TEXT,
            espesor         TEXT,
            color           TEXT,
            dimensiones     TEXT,   -- JSON array de strings
            cantidad        INTEGER,
            precio_total    REAL,
            accesorios      TEXT,   -- JSON array de strings
            observaciones   TEXT
        )
    """)

    # ------------------------------------------------------------------
    # TABLA: items_humano
    # Corrección del operador sobre cada mueble detectado por la IA.
    # Permite comparar campo a campo IA vs humano por ítem.
    # Clave académica: campos_corregidos / campos_totales = tasa de error del modelo.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_humano (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            captura_id          INTEGER NOT NULL REFERENCES capturas(id),
            item_ia_id          INTEGER REFERENCES items_ia(id),
            orden               INTEGER NOT NULL,
            producto            TEXT,
            material            TEXT,
            espesor             TEXT,
            color               TEXT,
            dimensiones         TEXT,   -- JSON array de strings
            cantidad            INTEGER,
            precio_total        REAL,
            accesorios          TEXT,   -- JSON array de strings
            observaciones       TEXT,
            -- Métricas de calidad HITL calculadas al guardar
            campos_totales      INTEGER DEFAULT 0,
            campos_corregidos   INTEGER DEFAULT 0,
            precision_item      REAL    -- 1 - (campos_corregidos / campos_totales)
        )
    """)

    # ------------------------------------------------------------------
    # TABLA: metricas_pipeline
    # Resumen de métricas por captura para análisis estadístico y defensa.
    # Esta tabla es la base de los gráficos académicos del sistema.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metricas_pipeline (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            captura_id              INTEGER NOT NULL REFERENCES capturas(id),
            timestamp               DATETIME DEFAULT CURRENT_TIMESTAMP,
            -- Métricas de tiempo
            latencia_total_ms       INTEGER,
            latencia_asr_ms         INTEGER,
            latencia_nlp_ms         INTEGER,
            -- Métricas de calidad del modelo
            num_items_ia            INTEGER DEFAULT 0,
            num_items_humano        INTEGER DEFAULT 0,
            campos_totales_captura  INTEGER DEFAULT 0,
            campos_corregidos_total INTEGER DEFAULT 0,
            precision_global        REAL,   -- 1 - (campos_corregidos / campos_totales)
            -- Labels detectados (para análisis de cobertura del NER)
            labels_encontrados      TEXT,   -- JSON array
            -- Observaciones
            notas                   TEXT
        )
    """)

    conn.commit()
    conn.close()
    logger.info("[DB] Base de datos inicializada correctamente.")


# =============================================================================
# SECCIÓN 2: HELPERS INTERNOS
# =============================================================================

def _json_lista(valor: Any) -> str:
    """Serializa listas a JSON string para almacenamiento en SQLite."""
    if isinstance(valor, list):
        return json.dumps(valor, ensure_ascii=False)
    if valor is None:
        return json.dumps([])
    return json.dumps([str(valor)], ensure_ascii=False)


def _calcular_metricas_item(item_ia: Dict, item_humano: Dict) -> Dict:
    """
    Calcula cuántos campos fueron corregidos por el operador en un ítem.
    Compara campo a campo IA vs humano.
    Retorna: {campos_totales, campos_corregidos, precision_item}

    Campos evaluables (excluye IDs y metadatos):
      producto, material, espesor, color, dimensiones, cantidad, precio_total, accesorios
    """
    CAMPOS_EVALUABLES = [
        "producto", "material", "espesor", "color",
        "dimensiones", "cantidad", "precio_total", "accesorios"
    ]

    campos_totales = 0
    campos_corregidos = 0

    for campo in CAMPOS_EVALUABLES:
        val_ia = item_ia.get(campo)
        val_humano = item_humano.get(campo)

        # Solo contar campos donde al menos uno tiene valor
        if val_ia is not None or val_humano is not None:
            campos_totales += 1
            # Normalizar para comparación: convertir a string lowercase
            str_ia = str(val_ia).lower().strip() if val_ia is not None else ""
            str_humano = str(val_humano).lower().strip() if val_humano is not None else ""
            if str_ia != str_humano:
                campos_corregidos += 1

    precision = 1.0 - (campos_corregidos / campos_totales) if campos_totales > 0 else 1.0

    return {
        "campos_totales": campos_totales,
        "campos_corregidos": campos_corregidos,
        "precision_item": round(precision, 4)
    }


# =============================================================================
# SECCIÓN 3: OPERACIONES DE ESCRITURA
# =============================================================================

def guardar_captura_inicial(
    texto_transcrito: str,
    texto_normalizado: str,
    modelo_version: str,
    latencia_total_ms: int,
    latencia_asr_ms: int,
    latencia_nlp_ms: int,
    num_items_ia: int,
    labels_detectados: List[str],
    advertencias_motor: List[str],
) -> int:
    """
    Guarda el registro principal de una captura de voz.
    Retorna el ID generado (captura_id) para usarlo en las tablas hijas.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO capturas (
                texto_transcrito, texto_normalizado, modelo_version,
                latencia_total_ms, latencia_asr_ms, latencia_nlp_ms,
                num_items_ia, labels_detectados, advertencias_motor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            texto_transcrito,
            texto_normalizado,
            modelo_version,
            latencia_total_ms,
            latencia_asr_ms,
            latencia_nlp_ms,
            num_items_ia,
            json.dumps(labels_detectados, ensure_ascii=False),
            json.dumps(advertencias_motor, ensure_ascii=False),
        ))
        conn.commit()
        captura_id = cursor.lastrowid
        logger.info(f"[DB] Captura guardada: id={captura_id}")
        return captura_id
    finally:
        conn.close()


def guardar_items_ia(captura_id: int, muebles_ia: List[Dict]) -> List[int]:
    """
    Guarda los ítems detectados por la IA para una captura.
    Retorna lista de IDs generados (item_ia_ids).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    item_ids: List[int] = []
    try:
        for orden, mueble in enumerate(muebles_ia):
            cursor.execute("""
                INSERT INTO items_ia (
                    captura_id, orden, producto, material, espesor, color,
                    dimensiones, cantidad, precio_total, accesorios, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                captura_id,
                orden,
                mueble.get("producto"),
                mueble.get("material"),
                mueble.get("espesor"),
                mueble.get("color"),
                _json_lista(mueble.get("dimensiones")),
                mueble.get("cantidad"),
                mueble.get("precio_total"),
                _json_lista(mueble.get("accesorios")),
                mueble.get("observaciones"),
            ))
            conn.commit()
            item_ids.append(cursor.lastrowid)
        logger.info(f"[DB] {len(item_ids)} ítems IA guardados para captura_id={captura_id}")
        return item_ids
    finally:
        conn.close()


def guardar_validacion_hitl(
    captura_id: int,
    items_ia_ids: List[int],
    muebles_ia: List[Dict],
    muebles_humano: List[Dict],
    latencia_total_ms: int,
    latencia_asr_ms: int,
    latencia_nlp_ms: int,
    labels_encontrados: List[str],
) -> Dict:
    """
    Guarda la validación humana (HITL) completa de una captura.
    Calcula métricas de calidad y las persiste en metricas_pipeline.

    Retorna un dict con las métricas calculadas para enviar al frontend.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_campos_captura = 0
    total_corregidos_captura = 0

    try:
        # Guardar cada ítem validado por el humano
        for orden, mueble_humano in enumerate(muebles_humano):
            # Obtener el ítem IA correspondiente por orden
            mueble_ia = muebles_ia[orden] if orden < len(muebles_ia) else {}
            item_ia_id = items_ia_ids[orden] if orden < len(items_ia_ids) else None

            metricas_item = _calcular_metricas_item(mueble_ia, mueble_humano)

            cursor.execute("""
                INSERT INTO items_humano (
                    captura_id, item_ia_id, orden,
                    producto, material, espesor, color,
                    dimensiones, cantidad, precio_total, accesorios, observaciones,
                    campos_totales, campos_corregidos, precision_item
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                captura_id,
                item_ia_id,
                orden,
                mueble_humano.get("producto"),
                mueble_humano.get("material"),
                mueble_humano.get("espesor"),
                mueble_humano.get("color"),
                _json_lista(mueble_humano.get("dimensiones")),
                mueble_humano.get("cantidad"),
                mueble_humano.get("precio_total"),
                _json_lista(mueble_humano.get("accesorios")),
                mueble_humano.get("observaciones"),
                metricas_item["campos_totales"],
                metricas_item["campos_corregidos"],
                metricas_item["precision_item"],
            ))

            total_campos_captura += metricas_item["campos_totales"]
            total_corregidos_captura += metricas_item["campos_corregidos"]

        # Calcular precisión global de la captura
        precision_global = (
            1.0 - (total_corregidos_captura / total_campos_captura)
            if total_campos_captura > 0 else 1.0
        )

        # Guardar métricas consolidadas
        cursor.execute("""
            INSERT INTO metricas_pipeline (
                captura_id, latencia_total_ms, latencia_asr_ms, latencia_nlp_ms,
                num_items_ia, num_items_humano,
                campos_totales_captura, campos_corregidos_total,
                precision_global, labels_encontrados
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            captura_id,
            latencia_total_ms,
            latencia_asr_ms,
            latencia_nlp_ms,
            len(muebles_ia),
            len(muebles_humano),
            total_campos_captura,
            total_corregidos_captura,
            round(precision_global, 4),
            json.dumps(labels_encontrados, ensure_ascii=False),
        ))

        conn.commit()
        logger.info(
            f"[DB] HITL guardado: captura_id={captura_id}, "
            f"precisión={precision_global:.2%}, "
            f"campos_corregidos={total_corregidos_captura}/{total_campos_captura}"
        )

        return {
            "campos_totales": total_campos_captura,
            "campos_corregidos": total_corregidos_captura,
            "precision_global": round(precision_global, 4),
            "tasa_correccion": round(
                total_corregidos_captura / total_campos_captura, 4
            ) if total_campos_captura > 0 else 0.0,
        }

    finally:
        conn.close()


# =============================================================================
# SECCIÓN 4: OPERACIONES DE LECTURA (para endpoint de métricas académicas)
# =============================================================================

def obtener_metricas_resumen() -> Dict:
    """
    Retorna un resumen estadístico de todas las capturas registradas.
    Útil para el panel académico y para la defensa de tesis.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                COUNT(*)                        AS total_capturas,
                AVG(precision_global)           AS precision_promedio,
                AVG(latencia_total_ms)          AS latencia_promedio_ms,
                AVG(latencia_asr_ms)            AS latencia_asr_promedio_ms,
                AVG(latencia_nlp_ms)            AS latencia_nlp_promedio_ms,
                SUM(campos_totales_captura)     AS campos_totales_acumulados,
                SUM(campos_corregidos_total)    AS campos_corregidos_acumulados,
                AVG(num_items_ia)               AS promedio_items_por_captura
            FROM metricas_pipeline
        """)
        row = cursor.fetchone()
        if not row or row[0] == 0:
            return {"mensaje": "Sin capturas registradas aún."}

        return {
            "total_capturas": row[0],
            "precision_promedio_modelo": round(row[1] or 0, 4),
            "latencia_total_promedio_ms": round(row[2] or 0, 1),
            "latencia_asr_promedio_ms": round(row[3] or 0, 1),
            "latencia_nlp_promedio_ms": round(row[4] or 0, 1),
            "campos_totales_acumulados": row[5] or 0,
            "campos_corregidos_acumulados": row[6] or 0,
            "tasa_error_promedio": round(
                (row[6] or 0) / (row[5] or 1), 4
            ),
            "promedio_items_por_captura": round(row[7] or 0, 2),
        }
    finally:
        conn.close()


def obtener_capturas_para_entrenamiento(solo_validadas: bool = True) -> List[Dict]:
    """
    Retorna capturas con su validación HITL para reentrenamiento del modelo.
    Formato compatible con el pipeline de anotación de spaCy.

    Solo devuelve capturas que tienen items_humano registrados (validadas).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                c.id,
                c.texto_transcrito,
                c.texto_normalizado,
                ih.orden,
                ih.producto,
                ih.material,
                ih.espesor,
                ih.color,
                ih.dimensiones,
                ih.cantidad,
                ih.precio_total,
                ih.accesorios,
                ih.observaciones
            FROM capturas c
            INNER JOIN items_humano ih ON c.id = ih.captura_id
            ORDER BY c.id, ih.orden
        """)
        rows = cursor.fetchall()
        columnas = [d[0] for d in cursor.description]
        return [dict(zip(columnas, row)) for row in rows]
    finally:
        conn.close()