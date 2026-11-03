"""Explicit, stateless catalog extraction. No SKU lookup or persistence.

Catalog identifiers and names are supplied by the consumer from active records.
Evidence always refers to the unchanged input; uncertain values stay unresolved.
"""

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from homex_nlp.contracts.evidence import Candidate
from homex_nlp.rules import (
    NUMBER_WORDS,
    decimal_from_text,
    is_explicitly_negated,
    money,
    price_mentions,
)

Category = Literal["SILLA", "PISO_FLOTANTE", "OTRO"]


class CatalogValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    concept: str
    code: str
    name: str
    synonyms: list[str] = Field(default_factory=list)


class CatalogRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Category
    text: str = Field(min_length=1, max_length=20000)
    values: list[CatalogValue] = Field(default_factory=list)


class CatalogResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Category
    fields: dict[str, str | int | dict] = Field(default_factory=dict)
    evidence: list[Candidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unrecognized: list[str] = Field(default_factory=list)
    version: str = "catalog-0.1.20"


def fold(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )


class Extractor:
    concepts = {"unidad_stock": "UNIDAD_MEDIDA"}

    def __init__(self, request):
        self.request = request
        self.result = CatalogResult(category=request.category)
        self.text = request.text

    def add(self, field, matches):
        accepted = []
        for start, end, value in sorted(set(matches), key=lambda x: x[0]):
            negated = is_explicitly_negated(self.text, start)
            candidate = Candidate(
                candidate_id=f"{field}-{start}-{end}",
                label=field,
                start=start,
                end=end,
                text=self.text[start:end],
                source="RULE",
                normalized_value=value,
                decision="REJECTED" if negated else "UNRESOLVED",
                reason="Negación explícita" if negated else None,
            )
            self.result.evidence.append(candidate)
            if not negated:
                # Corrections require an explicit marker between occurrences.
                if accepted and re.search(
                    r"\b(?:mejor|corrijo|perd[oó]n)\b", self.text[accepted[-1].end : start], re.I
                ):
                    for previous in accepted:
                        previous.decision = "REJECTED"
                        previous.reason = "Rectificación explícita"
                    accepted = []
                accepted.append(candidate)
        distinct = {str(c.normalized_value) for c in accepted}
        if len(distinct) == 1:
            self.result.fields[field] = accepted[-1].normalized_value
            for candidate in accepted:
                candidate.decision = "ACCEPTED"
        elif len(distinct) > 1:
            self.result.warnings.append(f"{field}: valores contradictorios; complete manualmente.")

    def labeled(self, field, pattern):
        self.add(
            field,
            [
                (m.start(1), m.end(1), m.group(1).strip())
                for m in re.finditer(pattern, self.text, re.I)
            ],
        )

    def catalogs(self):
        for field, concept in self.concepts.items():
            matches = []
            for value in self.request.values:
                if value.concept != concept:
                    continue
                aliases = {value.name, value.code.replace("_", " "), *value.synonyms}
                if concept == "UNIDAD_MEDIDA":
                    aliases.update(
                        {
                            "PIEZA": ["piezas", "pza", "pzas"],
                            "M2": ["m²", "metros cuadrados", "mts.2"],
                            "BARRA": ["barras"],
                            "JUEGO": ["juegos"],
                        }.get(value.code, [])
                    )
                for alias in aliases:
                    for m in re.finditer(
                        r"(?<!\w)" + re.escape(fold(alias)) + r"(?!\w)", fold(self.text)
                    ):
                        matches.append((m.start(), m.end(), value.id))
            self.add(field, matches)

    def extract(self):
        self.catalogs()
        self.labeled(
            "nombre",
            r"\b(?:nombre(?: comercial)?|producto)\s*(?::|es)?\s*"
            r"(.+?)(?=[.;\n]|\s+(?:modelo|marca|color|precio|unidad|descripci[oó]n|observaciones)\b|$)",
        )
        self.labeled("observaciones", r"\b(?:descripci[oó]n|observaciones)\s*(?::|es)?\s*([^\n]+)")
        mentions, _ = price_mentions(self.text)
        self.add(
            "precio_lista",
            [
                (m.start, m.end, money(m.value))
                for m, mode in mentions
                if mode == "PRECIO_UNITARIO" and m.value is not None
            ],
        )
        if "precio_lista" in self.result.fields:
            self.result.warnings.append(
                "Precio dictado: sugerencia pendiente de revisión comercial."
            )
        if re.search(
            r"\b(?:stock|existencias|total|cantidad|piezas|barras|metros cuadrados)\b",
            self.text,
            re.I,
        ):
            self.result.warnings.append(
                "Cantidades, existencias y totales no modifican inventario ni precio."
            )
        self.specific()
        if not self.result.fields:
            self.result.warnings.append(
                "Sin campos confiables: complete el formulario manualmente."
            )
        missing = [
            field
            for field in ("nombre", "unidad_stock", "precio_lista")
            if field not in self.result.fields
        ]
        if missing:
            self.result.warnings.append("Complete manualmente: " + ", ".join(missing))
        # Preserve every span not accepted as unresolved input (including unknown catalog terms).
        spans = sorted((c.start, c.end) for c in self.result.evidence if c.decision == "ACCEPTED")
        last = 0
        for start, end in spans:
            if start > last and self.text[last:start].strip(" ,.;:\n"):
                self.result.unrecognized.append(self.text[last:start])
            last = max(last, end)
        if self.text[last:].strip(" ,.;:\n"):
            self.result.unrecognized.append(self.text[last:])
        return self.result

    def specific(self):
        pass


class ChairExtractor(Extractor):
    concepts = {**Extractor.concepts, "marca": "MARCA", "color_primario": "COLOR"}

    def specific(self):
        self.labeled("modelo", r"\b(?:modelo|c[oó]digo|cod)\s*:?\s*([\w-]+)")
        specs = {}
        # These are physical features from HOMEX sources; no product identifiers.
        for name, pattern in {
            "apoyo_lumbar": r"apoyo lumbar|reposa lumbar|parte lumbar",
            "reposacabezas": r"reposa cabezas?|reposacabezas|reposa cabeza",
            "reposapies": r"reposa pi[eé]s|reposapi[eé]s",
            "brazos_regulables": r"(?:brazos|apoya brazos|reposa brazos) regulables?",
            "material_respaldo": r"malla",
            "tapiz": r"cuero ecol[oó]gico|tela repelente a l[ií]quidos|tapiz de alto tr[aá]fico",
            "asiento": r"espuma (?:inyectada|de alta densidad)|esponja de alta densidad",
            "suspension": r"suspensi[oó]n hidr[aá]ulica|pist[oó]n clase [1234]",
            "mecanismo": r"doble palanca|una palanca|sistema de rodilla",
            "capacidad": r"\d+\s*kg",
            "patas": r"(?:[1-9]|cinco|cuatro)\s+patas(?: con ruedas)?",
            "giro": r"360\s*(?:grados|º|°)",
            "base": r"base cromada|base de PVC|patas cromadas|nylon de alta resistencia",
        }.items():
            self.add(
                "especificaciones." + name,
                [
                    (m.start(), m.end(), m.group())
                    for m in re.finditer(r"\b(?:" + pattern + r")\b", self.text, re.I)
                ],
            )
            key = "especificaciones." + name
            if key in self.result.fields:
                specs[name] = self.result.fields.pop(key)
        if specs:
            self.result.fields["especificaciones"] = specs


class FloorExtractor(Extractor):
    concepts = {
        **Extractor.concepts,
        "marca": "MARCA",
        "tipo": "TIPO_PISO",
        "material": "MATERIAL_PISO",
        "diseno": "DISENO_PISO",
        "acabado": "ACABADO_PISO",
    }

    def specific(self):
        self.labeled("modelo", r"\b(?:modelo|c[oó]digo|cod)\s*:?\s*([\w-]+)")
        number = r"(?:\d+(?:[,.]\d+)?|" + "|".join(NUMBER_WORDS) + ")"
        for field, label in [
            ("espesor_mm", "espesor"),
            ("largo_mm", "largo"),
            ("ancho_mm", "ancho"),
        ]:
            matches = []
            patterns = [
                rf"\b{label}\s*(?:de|:)?\s*({number})\s*(mm|cm|mil[ií]metros?|cent[ií]metros?|metros?|m)\b"
            ]
            if field == "espesor_mm":
                patterns.append(
                    rf"\b({number})\s*(mm|cm|mil[ií]metros?|cent[ií]metros?)\s+de espesor\b"
                )
            for pattern in patterns:
                for m in re.finditer(pattern, self.text, re.I):
                    value = decimal_from_text(str(NUMBER_WORDS.get(m.group(1).lower(), m.group(1))))
                    if value:
                        factor = (
                            1
                            if (m.group(2).lower() == "mm" or fold(m.group(2)).startswith("mili"))
                            else 10
                            if (m.group(2).lower() == "cm" or fold(m.group(2)).startswith("centi"))
                            else 1000
                        )
                        matches.append((m.start(), m.end(), str(value * factor)))
            self.add(field, matches)
        self.add(
            "m2_por_caja",
            [
                (m.start(), m.end(), str(value))
                for m in re.finditer(
                    r"\b(\d+(?:[,.]\d+)?)\s*(?:m2|m²|metros cuadrados)\s+por caja\b",
                    self.text,
                    re.I,
                )
                if (value := decimal_from_text(m.group(1))) is not None
            ],
        )


class OtherExtractor(Extractor):
    """Heterogeneous products use explicit name/description and real unit catalog."""


def extract_catalog(request: CatalogRequest) -> CatalogResult:
    # Category is supplied exclusively by the selected form, never inferred.
    return {"SILLA": ChairExtractor, "PISO_FLOTANTE": FloorExtractor, "OTRO": OtherExtractor}[
        request.category
    ](request).extract()
