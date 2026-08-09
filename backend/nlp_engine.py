import spacy
from spacy.pipeline import EntityRuler
from pydantic import BaseModel, Field
from typing import Optional
import logging

from config import settings

# Configurar logging
logger = logging.getLogger(__name__)


# 1. Definimos el esquema de salida con Pydantic (Normalización)
class CotizacionMueble(BaseModel):
    producto: Optional[str] = Field(None, description="Tipo de mueble (ej. ropero, mesa)")
    material: Optional[str] = Field(None, description="Material base (ej. melamina, pino)")
    color: Optional[str] = Field(None, description="Color del material")
    dimensiones: list[str] = Field(default_factory=list, description="Medidas detectadas")


# 2. Inicializamos spaCy y agregamos reglas determinísticas (EntityRuler)
# Usamos un patrón singleton para evitar recargar el modelo múltiples veces
_nlp = None

def obtener_nlp():
    """Obtiene la instancia de spaCy cargada una sola vez"""
    global _nlp
    if _nlp is None:
        logger.info("Cargando modelo spaCy 'es_core_news_sm'...")
        _nlp = spacy.load("es_core_news_sm")
        
        # Configuramos el Ruler ANTES del NER estadístico para darle prioridad
        ruler = _nlp.add_pipe("entity_ruler", before="ner")
        
        # Definimos patrones de diccionario (Esto simula tu conocimiento del dominio)
        patrones = [
            # Reglas para Materiales
            {"label": "MATERIAL", "pattern": [{"LOWER": "melamina"}]},
            {"label": "MATERIAL", "pattern": [{"LOWER": "mdf"}]},
            {"label": "MATERIAL", "pattern": [{"LOWER": "pino"}]},
            # Reglas para Productos
            {"label": "PRODUCTO", "pattern": [{"LOWER": "ropero"}]},
            {"label": "PRODUCTO", "pattern": [{"LOWER": "escritorio"}]},
            # Reglas Regex para Dimensiones (ej. "2 metros", "150 centimetros", "1.5 m")
            {"label": "DIMENSION", "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["metros", "metro", "centimetros", "cm", "m"]}}]}
        ]
        ruler.add_patterns(patrones)
        
        logger.info("Modelo spaCy cargado exitosamente.")
    
    return _nlp


def procesar_texto(texto: str) -> dict:
    """
    Procesa el texto y devuelve un JSON estructurado.
    
    Args:
        texto: Texto transcrito del audio
        
    Returns:
        dict: Datos extraídos en formato estructurado
        
    Raises:
        ValueError: Si el texto está vacío o es None
    """
    # Validación de entrada
    if not texto or not texto.strip():
        logger.warning("Se recibió texto vacío para procesamiento")
        raise ValueError("El texto de entrada está vacío")
    
    try:
        nlp = obtener_nlp()
        doc = nlp(texto.lower())
        
        resultado = CotizacionMueble()
        
        for ent in doc.ents:
            if ent.label_ == "PRODUCTO" and not resultado.producto:
                resultado.producto = ent.text
            elif ent.label_ == "MATERIAL" and not resultado.material:
                resultado.material = ent.text
            elif ent.label_ == "DIMENSION":
                resultado.dimensiones.append(ent.text)
                
        # Aquí podríamos agregar reglas heurísticas para el color
        # (ej. si la palabra "blanco" está cerca de "melamina")
        
        logger.info(f"Entidades extraídas: producto={resultado.producto}, material={resultado.material}, dimensiones={len(resultado.dimensiones)}")
        
        return resultado.model_dump()
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento NLP: {str(e)}")
        raise