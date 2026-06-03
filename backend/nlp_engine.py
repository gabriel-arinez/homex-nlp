# =============================================================================
# nlp_engine.py — HOMEX NLP Engine v4.0
# Motor NLP central del aporte académico.
# Responsabilidades: normalización, extracción NER, estructuración de
# CotizacionCapturada con soporte real para múltiples muebles por cotización.
#
# Arquitectura:
#   TextoNormalizado → spaCy NER → Segmentador → [DetalleMueble, ...] → CotizacionCapturada
#
# NOTAS DE DISEÑO:
# - El modelo spaCy puede ser estadístico (model-best entrenado) o de reglas
#   (EntityRuler fallback). El motor es agnóstico a cuál está activo.
# - La normalización es PRE-NER: se hace sobre texto crudo antes de pasarlo
#   al modelo, resolviendo variantes del español boliviano (coma decimal, abreviaturas).
# - La segmentación de múltiples muebles usa conectores textuales detectados
#   en el texto normalizado, NO en el output del NER.
# - Pydantic valida la estructura de salida; nunca se retorna un dict plano
#   sin pasar por el schema.
# =============================================================================

import re
import logging
from typing import Optional, List, Tuple

import spacy
from spacy.language import Language
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# SECCIÓN 1: SCHEMAS PYDANTIC
# Representan el contrato de datos entre el motor NLP, el backend y el frontend.
# DetalleMueble → un solo ítem de la cotización.
# CotizacionCapturada → contenedor raíz que siempre devuelve el motor.
# =============================================================================

class DetalleMueble(BaseModel):
    """
    Representa un único mueble o ítem dentro de una cotización.
    Todos los campos son opcionales: el motor puede detectar algunos o ninguno
    dependiendo del texto y el estado del modelo NER.
    """
    producto: Optional[str] = Field(
        None,
        description="Nombre del mueble o producto. Ej: ESCRITORIO EJECUTIVO, CLOSET CAJONERIA"
    )
    material: Optional[str] = Field(
        None,
        description="Material base. Ej: Melamina, MDF, Madera Pino"
    )
    espesor: Optional[str] = Field(
        None,
        description="Espesor del material en mm. Ej: 18 mm, 25 mm"
    )
    color: Optional[str] = Field(
        None,
        description="Color o acabado superficial. Ej: Blanco, Nogal, Wengue"
    )
    dimensiones: List[str] = Field(
        default_factory=list,
        description="Lista de medidas individuales detectadas. Ej: ['1.80 metros ancho', '0.80 metros alto']"
    )
    cantidad: Optional[int] = Field(
        None,
        description="Cantidad de unidades solicitadas. Ej: 1, 2, 3"
    )
    precio_total: Optional[float] = Field(
        None,
        description="Precio total del ítem si se menciona. Ej: 1700.0"
    )
    accesorios: List[str] = Field(
        default_factory=list,
        description="Herrajes, mecanismos y accesorios. Ej: rieles telescopicas, bisagras pispot"
    )
    observaciones: Optional[str] = Field(
        None,
        description="Texto libre con indicaciones técnicas no estructuradas. Ej: Según diseño"
    )

    def tiene_datos(self) -> bool:
        """Retorna True si el mueble tiene al menos un campo con valor."""
        return any([
            self.producto, self.material, self.espesor, self.color,
            self.dimensiones, self.cantidad, self.precio_total,
            self.accesorios, self.observaciones
        ])


class CotizacionCapturada(BaseModel):
    """
    Contenedor raíz. Siempre se retorna este objeto, nunca un DetalleMueble suelto.
    Permite que una sola grabación de voz contenga N muebles.
    """
    texto_original: str = Field(
        description="Texto transcrito por Whisper, sin modificar."
    )
    texto_normalizado: str = Field(
        description="Texto después de normalización previa al NER."
    )
    muebles: List[DetalleMueble] = Field(
        default_factory=list,
        description="Lista de muebles detectados en la cotización."
    )
    num_items_detectados: int = Field(
        0,
        description="Cantidad de muebles detectados por la IA."
    )
    labels_detectados: List[str] = Field(
        default_factory=list,
        description="Etiquetas NER encontradas en el texto. Útil para debugging académico."
    )
    advertencias: List[str] = Field(
        default_factory=list,
        description="Mensajes de advertencia del motor. Ej: offset inválido, entidad ambigua."
    )


# =============================================================================
# SECCIÓN 2: NORMALIZADOR DE TEXTO
# Responsabilidad única: preparar el texto crudo para el modelo NER.
# Maneja variantes reales encontradas en los ejemplos de HOMEX:
#   - Coma decimal boliviana: 0,80 → 0.80
#   - Abreviaturas de unidades: mts → metros, cm → centimetros, mm → milimetros
#   - Separación de número pegado a unidad: "18mm" → "18 mm"
#   - Normalización de conectores de segmentación
# IMPORTANTE: la normalización NO lowercasea el texto antes del NER estadístico
# porque el modelo entrenado puede usar mayúsculas como señal (ESCRITORIO EJECUTIVO).
# El lowercase se aplica solo para búsquedas de patrones heurísticos internos.
# =============================================================================

# Conectores que indican el inicio de un nuevo mueble en la misma cotización.
# Derivados del análisis de los pedidos reales.
_CONECTORES_SEGMENTACION = [
    r'\n(?=[A-ZÁÉÍÓÚÑ]{3,})',          # Salto de línea seguido de mayúsculas (como en los pedidos reales)
    r'(?i)\by\s+también\b',
    r'(?i)\bademás\b',
    r'(?i)\btambién\s+necesito\b',
    r'(?i)\by\s+un[ao]?\b',
    r'(?i)\by\s+(?=\d+\s)',             # "y 2 veladores"
]

def normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto crudo para maximizar la detección NER.
    Opera sobre el texto ANTES de pasarlo al modelo spaCy.

    Transformaciones aplicadas (en orden):
    1. Coma decimal boliviana: 0,80 → 0.80 (solo cuando está entre dígitos)
    2. Número pegado a unidad: 18mm → 18 mm, 0.80mts → 0.80 mts
    3. Abreviaturas de unidades (límite de palabra para no afectar palabras con esas letras)
    4. Normalización de "segun diseño" → observación estándar
    5. Limpieza de espacios múltiples
    """
    t = texto

    # 1. Coma decimal boliviana: "0,80" → "0.80"
    #    Solo aplica cuando hay dígitos en ambos lados de la coma
    t = re.sub(r'(\d),(\d)', r'\1.\2', t)

    # 2. Número pegado a unidad sin espacio: "18mm" → "18 mm", "1.80mts" → "1.80 mts"
    t = re.sub(r'(\d)(mm|cm|mts|mts\.|m\b)', r'\1 \2', t)

    # 3. Abreviaturas de unidades (límites de palabra \b para no afectar otras palabras)
    t = re.sub(r'\bmts\.?\b', 'metros', t, flags=re.IGNORECASE)
    t = re.sub(r'\bcms?\b', 'centimetros', t, flags=re.IGNORECASE)
    t = re.sub(r'\bmm\b', 'milimetros', t, flags=re.IGNORECASE)

    # 4. Variante de escritura del espesor: "a 25 mm" → ya normalizado arriba
    #    Texto: "meson engrosado a 25 milimetros" — se deja para el NER

    # 5. Normalizar "segun diseño" como observación reconocible
    t = re.sub(r'(?i)seg[uú]n\s+dise[ñn]o\.?', 'SEGUN_DISEÑO', t)

    # 6. Limpieza de espacios múltiples
    t = re.sub(r'[ \t]{2,}', ' ', t)
    t = t.strip()

    return t


def segmentar_multiples_muebles(texto: str) -> List[str]:
    """
    Divide un texto de cotización en segmentos, donde cada segmento
    corresponde a un mueble independiente.

    Estrategia principal: detectar líneas que comienzan con mayúsculas sostenidas
    (como los encabezados de los pedidos reales: "ESCRITORIO EJECUTIVO", "CREDENZA").
    Estrategia secundaria: conectores textuales explícitos.

    Retorna: lista de strings, uno por mueble detectado.
    Si no se puede segmentar, retorna [texto_completo] para procesarlo como uno solo.
    """
    # Estrategia 1: Segmentación por bloques de texto con encabezado en MAYÚSCULAS
    # Patrón observado en los 3 ejemplos reales: cada mueble empieza con su nombre en mayúsculas
    # seguido de descripción en minúsculas/mixto.
    # Detectamos líneas que son predominantemente mayúsculas (nombre del producto)
    lineas = texto.split('\n')
    segmentos: List[str] = []
    segmento_actual: List[str] = []

    for linea in lineas:
        linea_stripped = linea.strip()
        if not linea_stripped:
            continue

        # Una línea es "encabezado de mueble" si:
        # - Tiene al menos 3 caracteres
        # - Más del 60% de sus letras son mayúsculas
        # - No empieza con "Tamaño", "total", "cantidad" (son descriptores, no encabezados)
        letras = [c for c in linea_stripped if c.isalpha()]
        mayusculas = [c for c in letras if c.isupper()]
        es_encabezado = (
            len(letras) >= 3
            and len(letras) > 0
            and (len(mayusculas) / len(letras)) > 0.6
            and not re.match(r'(?i)^(tamaño|total|cantidad|segun|incluye)', linea_stripped)
        )

        if es_encabezado and segmento_actual:
            # Guardar el segmento anterior y empezar uno nuevo
            segmentos.append('\n'.join(segmento_actual).strip())
            segmento_actual = [linea_stripped]
        else:
            segmento_actual.append(linea_stripped)

    if segmento_actual:
        segmentos.append('\n'.join(segmento_actual).strip())

    # Si la segmentación no encontró divisiones, retornar el texto como un solo bloque
    if not segmentos:
        return [texto.strip()]

    # Filtrar segmentos vacíos
    return [s for s in segmentos if s.strip()]


# =============================================================================
# SECCIÓN 3: EXTRACTORES HEURÍSTICOS DE SOPORTE
# Estos extractores operan como POST-PROCESADORES sobre el texto normalizado.
# No reemplazan al NER estadístico: lo complementan para entidades que
# tienen patrones muy regulares (números, precios) o que el NER puede perder
# por falta de datos de entrenamiento.
# Cuando el modelo NER esté bien entrenado, estos siguen siendo válidos como
# validadores y como extracción de entidades numéricas.
# =============================================================================

def extraer_dimensiones_heuristica(texto: str) -> List[str]:
    """
    Extrae medidas del texto usando regex.
    Maneja los patrones reales observados en los pedidos HOMEX:
      - "1.80 metros de ancho"
      - "0.80 metros de alto"
      - "0.60 de profundidad" (sin unidad explícita — valor ambiguo)
      - "0.49 metros de ancho"
    """
    dimensiones: List[str] = []

    # Patrón completo: número + unidad + etiqueta de dimensión
    patron_completo = re.compile(
        r'(\d+\.?\d*)\s*(metros?|centimetros?|milimetros?)\s*(?:de\s+)?(ancho|alto|profundidad|fondo|largo)?',
        re.IGNORECASE
    )
    for m in patron_completo.finditer(texto):
        valor = m.group(1)
        unidad = m.group(2)
        etiqueta = m.group(3) or ''
        dimension = f"{valor} {unidad}"
        if etiqueta:
            dimension += f" {etiqueta}"
        dimensiones.append(dimension.strip())

    # Patrón sin unidad explícita: "0.60 de profundidad"
    patron_sin_unidad = re.compile(
        r'(\d+\.?\d*)\s+de\s+(ancho|alto|profundidad|fondo|largo)',
        re.IGNORECASE
    )
    for m in patron_sin_unidad.finditer(texto):
        # Solo agregar si no fue capturado ya por el patrón completo
        candidato = f"{m.group(1)} {m.group(2)}"
        if not any(m.group(1) in d for d in dimensiones):
            dimensiones.append(candidato)

    return dimensiones


def extraer_espesor_heuristica(texto: str) -> Optional[str]:
    """
    Extrae el espesor del material.
    Patrones reales:
      - "melamina de 18 milimetros"
      - "meson engrosado a 25 milimetros"
      - "melamina de 18 mm" (antes de normalizar)
    """
    patron = re.compile(
        r'(?:de|a)\s+(\d+)\s*milimetros',
        re.IGNORECASE
    )
    m = patron.search(texto)
    if m:
        return f"{m.group(1)} mm"
    return None


def extraer_precio_heuristica(texto: str) -> Optional[float]:
    """
    Extrae el precio total si se menciona.
    Patrón real: "total 1700", "total 2800", "total 1500"
    """
    patron = re.compile(r'(?i)\btotal\s+(\d+(?:\.\d+)?)\b')
    m = patron.search(texto)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def extraer_cantidad_heuristica(texto: str) -> Optional[int]:
    """
    Extrae la cantidad de unidades.
    Patrón real: "cantidad 1", "cantidad 2"
    También detecta: "dos veladores", "3 unidades"
    """
    # Patrón directo: "cantidad N"
    patron_directo = re.compile(r'(?i)\bcantidad\s+(\d+)\b')
    m = patron_directo.search(texto)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass

    # Patrón numérico al inicio de frase tipo "2 closets"
    patron_inicio = re.compile(r'(?i)^(\d+)\s+\w+', re.MULTILINE)
    m = patron_inicio.search(texto)
    if m:
        val = int(m.group(1))
        if 1 <= val <= 99:  # Rango razonable de cantidad
            return val

    return None


def extraer_observaciones(texto: str) -> Optional[str]:
    """
    Captura el marcador "SEGUN_DISEÑO" que fue normalizado previamente.
    """
    if 'SEGUN_DISEÑO' in texto:
        return 'Según diseño'
    return None


def extraer_accesorios_heuristica(texto: str) -> List[str]:
    """
    Extrae accesorios y herrajes usando un diccionario del dominio.
    Derivado directamente de los ejemplos reales de HOMEX.
    Funciona como fallback si el NER no tiene suficientes ejemplos de ACCESORIO.
    """
    # Diccionario derivado de los 3 pedidos reales + conocimiento del dominio
    ACCESORIOS_DOMINIO = [
        r'rieles?\s+telescopicas?',
        r'jaladores?\s+met[aá]licos?',
        r'chapa\s+de\s+seguridad(?:\s+frontal)?',
        r'bisagras?\s+pispot',
        r'bisagras?\s+(?:ocultas?|pispot|europeas?)?',
        r'bandeja\s+de\s+separaci[oó]n\s+(?:movible|fija)?',
        r'puertas?\s+batientes?',
        r'cajoner[ií]a\s+(?:fija|m[oó]vil)?',
        r'pasacable',
        r'tapacanteadas?\s+en\s+pvc',
        r'soporte\s+central',
        r'base\s+met[aá]lica',
        r'ruedas?',
        r'apoya\s+brazos?\s+regulable',
        r'cabezera\s+regulable',
        r'parte\s+lumbar\s+ajustable',
        r'doble\s+palanca',
        r'respaldo\s+inclinable',
    ]

    accesorios_encontrados: List[str] = []
    texto_lower = texto.lower()

    for patron in ACCESORIOS_DOMINIO:
        m = re.search(patron, texto_lower)
        if m:
            # Recuperar texto original con capitalización
            inicio = m.start()
            fin = m.end()
            accesorio = texto[inicio:fin].strip()
            accesorios_encontrados.append(accesorio.capitalize())

    return accesorios_encontrados


# =============================================================================
# SECCIÓN 4: MOTOR NLP — CLASE PRINCIPAL
# Implementa el patrón Facade: el backend solo necesita conocer
# MotorNLP.procesar_cotizacion(texto) → CotizacionCapturada
#
# Internamente orquesta:
#   1. Normalización
#   2. Segmentación de muebles
#   3. NER estadístico (spaCy model-best)
#   4. Extractores heurísticos como complemento y validación
#   5. Ensamblaje de CotizacionCapturada
# =============================================================================

class MotorNLP:
    """
    Motor NLP principal. Se instancia una sola vez al arrancar el servidor (singleton).
    Carga el modelo spaCy entrenado en __init__ y lo mantiene en memoria.

    Si el modelo entrenado no está disponible, carga el modelo base con
    EntityRuler como fallback para que el sistema no rompa durante desarrollo.
    """

    # Etiquetas NER que el modelo entrenado DEBE reconocer.
    # Derivadas del análisis de los ejemplos reales de HOMEX.
    # Estas mismas etiquetas deben usarse al anotar en Doccano.
    LABELS_ESPERADOS = {
        "PRODUCTO",    # ESCRITORIO EJECUTIVO, CREDENZA MESA AUXILIAR, CLOSET CAJONERIA
        "MATERIAL",    # melamina, pino, MDF, madera
        "ESPESOR",     # 18 mm, 25 mm (del material, no del mueble)
        "COLOR",       # blanco, nogal, wengue, natural
        "DIMENSION",   # 1.80 metros ancho, 0.80 metros alto
        "CANTIDAD",    # 1, 2, tres
        "ACCESORIO",   # rieles telescopicas, bisagras pispot, pasacable
        "PRECIO",      # total 1700
        "ACABADO",     # laca mate, barniz, malla (sillas)
    }

    def __init__(self, ruta_modelo: str = "../data/modelos_entrenados/model-best"):
        self.ruta_modelo = ruta_modelo
        self.nlp: Optional[Language] = None
        self._cargar_modelo()

    def _cargar_modelo(self) -> None:
        """
        Intenta cargar el modelo NER entrenado.
        Si falla (no existe aún), carga modelo base con EntityRuler como fallback.
        Esto permite que el sistema funcione durante desarrollo sin modelo entrenado.
        """
        import os
        if os.path.exists(self.ruta_modelo):
            try:
                self.nlp = spacy.load(self.ruta_modelo)
                logger.info(f"[NLP] Modelo entrenado cargado desde: {self.ruta_modelo}")
                print(f"[IA] Modelo NER HOMEX cargado: {self.ruta_modelo}")
                return
            except Exception as e:
                logger.warning(f"[NLP] Error al cargar modelo entrenado: {e}. Usando fallback.")

        # Fallback: modelo base + EntityRuler con patrones del dominio
        self.nlp = self._construir_modelo_fallback()
        logger.info("[NLP] Usando modelo fallback con EntityRuler (sin entrenamiento NER).")
        print("[IA] ADVERTENCIA: Usando EntityRuler fallback. Entrena el modelo NER para producción.")

    def _construir_modelo_fallback(self) -> Language:
        """
        Construye un pipeline spaCy con EntityRuler usando patrones del dominio.
        Se activa cuando el modelo entrenado no está disponible.
        Los patrones se derivan directamente de los ejemplos reales de HOMEX.
        """
        try:
            nlp = spacy.load("es_core_news_sm")
        except OSError:
            nlp = spacy.blank("es")
            logger.warning("[NLP] es_core_news_sm no instalado. Usando modelo en blanco.")

        # Si ya hay NER estadístico, agregar EntityRuler ANTES para que tenga prioridad
        if "ner" in nlp.pipe_names:
            ruler = nlp.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": True})
        else:
            ruler = nlp.add_pipe("entity_ruler")

        patrones_fallback = [
            # PRODUCTOS (nombres compuestos reales de los ejemplos)
            {"label": "PRODUCTO", "pattern": [{"LOWER": "escritorio"}, {"LOWER": "ejecutivo"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "credenza"}, {"LOWER": "mesa"}, {"LOWER": "auxiliar"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "credenza"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "silla"}, {"LOWER": "ejecutiva"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "closet"}, {"LOWER": {"REGEX": "\\d+"}}, {"LOWER": "cajoneria"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "closet"}, {"LOWER": "cajoneria"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "ropero"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "escritorio"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "mesa"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "estante"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "librero"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "cajonera"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "comoda"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "velador"}]},
            # MATERIALES
            {"label": "MATERIAL", "pattern": [{"LOWER": "melamina"}]},
            {"label": "MATERIAL", "pattern": [{"LOWER": "mdf"}]},
            {"label": "MATERIAL", "pattern": [{"LOWER": "pino"}]},
            {"label": "MATERIAL", "pattern": [{"LOWER": "madera"}]},
            {"label": "MATERIAL", "pattern": [{"LOWER": "madera"}, {"LOWER": "pino"}]},
            {"label": "MATERIAL", "pattern": [{"LOWER": "aglomerado"}]},
            # COLORES
            {"label": "COLOR", "pattern": [{"LOWER": "blanco"}]},
            {"label": "COLOR", "pattern": [{"LOWER": "blanca"}]},
            {"label": "COLOR", "pattern": [{"LOWER": "nogal"}]},
            {"label": "COLOR", "pattern": [{"LOWER": "wengue"}]},
            {"label": "COLOR", "pattern": [{"LOWER": "natural"}]},
            {"label": "COLOR", "pattern": [{"LOWER": "gris"}]},
            {"label": "COLOR", "pattern": [{"LOWER": "negro"}]},
            # DIMENSIONES (con unidad ya normalizada)
            {"label": "DIMENSION", "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["metros", "metro", "centimetros", "centimetro", "milimetros", "milimetro"]}}]},
        ]

        ruler.add_patterns(patrones_fallback)
        return nlp

    def _ensamblar_mueble_desde_ner(
        self,
        doc,
        texto_segmento: str,
        advertencias: List[str]
    ) -> DetalleMueble:
        """
        Construye un DetalleMueble combinando:
        1. Entidades del NER estadístico (prioridad)
        2. Extractores heurísticos como complemento (para lo que el NER no capturó)

        Cada extractor heurístico solo activa si el campo correspondiente
        quedó vacío después del NER. Esto evita duplicados.
        """
        mueble = DetalleMueble()

        # Registro de labels encontrados (para CotizacionCapturada.labels_detectados)
        labels_encontrados: List[str] = []

        # --- NER estadístico ---
        dimensiones_ner: List[str] = []

        for ent in doc.ents:
            labels_encontrados.append(ent.label_)

            if ent.label_ == "PRODUCTO" and not mueble.producto:
                mueble.producto = ent.text.strip().upper()

            elif ent.label_ == "MATERIAL" and not mueble.material:
                mueble.material = ent.text.strip().capitalize()

            elif ent.label_ == "ESPESOR" and not mueble.espesor:
                mueble.espesor = ent.text.strip()

            elif ent.label_ == "COLOR" and not mueble.color:
                mueble.color = ent.text.strip().capitalize()

            elif ent.label_ == "DIMENSION":
                dimensiones_ner.append(ent.text.strip())

            elif ent.label_ == "CANTIDAD" and not mueble.cantidad:
                try:
                    mueble.cantidad = int(re.search(r'\d+', ent.text).group())
                except (AttributeError, ValueError):
                    advertencias.append(f"No se pudo convertir cantidad: {ent.text!r}")

            elif ent.label_ == "PRECIO" and not mueble.precio_total:
                try:
                    mueble.precio_total = float(re.search(r'[\d.]+', ent.text).group())
                except (AttributeError, ValueError):
                    advertencias.append(f"No se pudo convertir precio: {ent.text!r}")

            elif ent.label_ == "ACCESORIO":
                accesorio = ent.text.strip().capitalize()
                if accesorio not in mueble.accesorios:
                    mueble.accesorios.append(accesorio)

            elif ent.label_ == "ACABADO" and not mueble.observaciones:
                mueble.observaciones = ent.text.strip()

        if dimensiones_ner:
            mueble.dimensiones = dimensiones_ner

        # --- Complemento heurístico (solo si el NER dejó campos vacíos) ---
        texto_lower = texto_segmento.lower()

        if not mueble.dimensiones:
            dims = extraer_dimensiones_heuristica(texto_segmento)
            if dims:
                mueble.dimensiones = dims
                advertencias.append("Dimensiones extraídas por heurística (NER no detectó DIMENSION).")

        if not mueble.espesor:
            esp = extraer_espesor_heuristica(texto_segmento)
            if esp:
                mueble.espesor = esp
                advertencias.append("Espesor extraído por heurística.")

        if not mueble.precio_total:
            precio = extraer_precio_heuristica(texto_segmento)
            if precio is not None:
                mueble.precio_total = precio

        if not mueble.cantidad:
            cant = extraer_cantidad_heuristica(texto_segmento)
            if cant is not None:
                mueble.cantidad = cant

        if not mueble.accesorios:
            accs = extraer_accesorios_heuristica(texto_segmento)
            if accs:
                mueble.accesorios = accs
                advertencias.append("Accesorios extraídos por heurística (NER no detectó ACCESORIO).")

        obs = extraer_observaciones(texto_segmento)
        if obs and not mueble.observaciones:
            mueble.observaciones = obs

        return mueble

    def procesar_cotizacion(self, texto: str) -> CotizacionCapturada:
        """
        Punto de entrada principal del motor NLP.
        Recibe el texto transcrito por Whisper y retorna una CotizacionCapturada
        con todos los muebles detectados.

        Flujo:
          texto_crudo
            → normalizar_texto()
            → segmentar_multiples_muebles()
            → para cada segmento: spaCy NER + heurísticas
            → CotizacionCapturada
        """
        advertencias: List[str] = []
        labels_globales: List[str] = []

        # 1. Normalización
        texto_norm = normalizar_texto(texto)

        # 2. Segmentación de múltiples muebles
        segmentos = segmentar_multiples_muebles(texto_norm)

        if len(segmentos) > 1:
            advertencias.append(f"Cotización segmentada en {len(segmentos)} mueble(s).")

        # 3. Procesamiento NER por segmento
        muebles: List[DetalleMueble] = []

        for i, segmento in enumerate(segmentos):
            try:
                doc = self.nlp(segmento)
                mueble = self._ensamblar_mueble_desde_ner(doc, segmento, advertencias)

                # Registrar labels encontrados en este segmento
                for ent in doc.ents:
                    if ent.label_ not in labels_globales:
                        labels_globales.append(ent.label_)

                if mueble.tiene_datos():
                    muebles.append(mueble)
                else:
                    advertencias.append(f"Segmento {i+1} no produjo entidades válidas. Revisar texto.")

            except Exception as e:
                logger.error(f"[NLP] Error al procesar segmento {i+1}: {e}")
                advertencias.append(f"Error en segmento {i+1}: {str(e)}")

        # Si no se extrajo ningún mueble, retornar objeto vacío con advertencia
        if not muebles:
            advertencias.append("El motor no detectó ningún mueble en el texto.")
            muebles = [DetalleMueble()]

        return CotizacionCapturada(
            texto_original=texto,
            texto_normalizado=texto_norm,
            muebles=muebles,
            num_items_detectados=len(muebles),
            labels_detectados=labels_globales,
            advertencias=advertencias,
        )