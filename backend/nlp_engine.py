import spacy
from spacy.pipeline import EntityRuler
from pydantic import BaseModel, Field
from typing import Optional

# 1. Definimos el esquema de salida con Pydantic (Normalización)
class CotizacionMueble(BaseModel):
    producto: Optional[str] = Field(None, description="Tipo de mueble (ej. ropero, mesa)")
    material: Optional[str] = Field(None, description="Material base (ej. melamina, pino)")
    color: Optional[str] = Field(None, description="Color del material")
    dimensiones: list[str] = Field(default_factory=list, description="Medidas detectadas")

# 2. Inicializamos spaCy y agregamos reglas determinísticas (EntityRuler)
nlp = spacy.load("es_core_news_sm")

# Configuramos el Ruler ANTES del NER estadístico para darle prioridad
ruler = nlp.add_pipe("entity_ruler", before="ner")

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

def procesar_texto(texto: str) -> dict:
    """Procesa el texto y devuelve un JSON estructurado"""
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
    
    return resultado.model_dump()

# --- PRUEBA EN CONSOLA ---
if __name__ == "__main__":
    texto_prueba = "Necesito un ropero de melamina de 2 metros de alto y 150 centimetros de ancho"
    print("Texto:", texto_prueba)
    print("Extracción:", procesar_texto(texto_prueba))