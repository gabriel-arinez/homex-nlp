"""Explicit, stateless catalog extraction. No SKU lookup or persistence.

Catalog identifiers and names are supplied by the consumer from active records.
Evidence always refers to the unchanged input; uncertain values stay unresolved.
"""

import re
import unicodedata
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from homex_nlp.contracts.evidence import Candidate
from homex_nlp.monetary import AMOUNT, cardinal
from homex_nlp.rules import (
    _numero_es_medida_no_precio,
    decimal_from_text,
    is_explicitly_negated,
    monetary_amount,
    money,
    price_mentions,
)
from homex_nlp.spoken_codes import _spoken_code_status

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
    version: str = "catalog-0.1.24"


def fold(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )


def alias_matches(text, alias):
    # Normalization can shorten decomposed Unicode: map each normalized character
    # back to its original span rather than using normalized offsets as originals.
    normalized, starts, ends = [], [], []
    for index, character in enumerate(text):
        folded = fold(character)
        if not folded and ends:
            ends[-1] = index + 1
        for letter in folded:
            normalized.append(letter)
            starts.append(index)
            ends.append(index + 1)
    for match in re.finditer(r"(?<!\w)" + re.escape(fold(alias)) + r"(?!\w)", "".join(normalized)):
        yield starts[match.start()], ends[match.end() - 1]


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
                    for start, end in alias_matches(self.text, alias):
                        matches.append((start, end, value.id))
            self.add(field, matches)

    def extract(self):
        self.catalogs()
        self.labeled(
            "nombre",
            r"\b(?:nombre(?: comercial)?|producto)\b\s*(?::|es)?\s*"
            r"(.+?)(?=[,.;\n]|\s+(?:mejor|corrijo|perd[oó]n|modelo|marca|color|precio|unidad|descripci[oó]n|observaciones)\b|$)",
        )
        if "nombre" not in self.result.fields:
            # Only an initial noun phrase or an explicit introduction is a name.
            # Technical and commercial clauses are kept out of this phrase.
            self.labeled(
                "nombre",
                r"^\s*(?:(?:quiero registrar|registrar|agregar|crear|se llama)\s+(?:un[ao]?\s+)?)?"
                # ASR may spell an initial count as digits. Keep the literal phrase,
                # without turning a standalone measurement/amount into a product.
                r"((?!\d+\s+(?:mm|cm|m|mil[ií]metros?|cent[ií]metros?|metros?|"
                r"bolivianos?|BOB|Bs|USD|d[oó]lares?)\b)(?:[1-9]\d*\s+)?"
                r"(?!no\b|sin\b|nombres?\b|modelos?\b|color\b|marca\b|precio\b|cantidad\b|stock\b|total\b|espesor\b)"
                r"[a-záéíóúñ][\wáéíóúñ -]*?)"
                r"(?=\s+(?:de\s+(?:malla|espuma|estructura|patas|madera|aglomerado|melamina|MDF|HDF|PVC|metal|acero)|con|modelo|c[oó]digo|color|marca|precio|espesor|largo|ancho)\b"
                r"|\s+(?:de\s+)?(?:\d|"
                + AMOUNT
                + r"\s*(?:mm|cm|m|mil[ií]metros?|cent[ií]metros?|metros?)\b)|[.;,:\n]|$)",
            )
            # Preserve the literal description, including heterogeneous specifications.
            if "nombre" in self.result.fields:
                for evidence in self.result.evidence:
                    if evidence.label == "nombre" and evidence.decision == "ACCEPTED":
                        evidence.reason = (
                            "Nombre delimitado antes de especificaciones técnicas o comerciales"
                        )
                self.add("observaciones", [(0, len(self.text), self.text)])
        if "observaciones" not in self.result.fields:
            self.labeled(
                "observaciones", r"\b(?:descripci[oó]n|observaciones)\b\s*(?::|es)?\s*([^\n]+)"
            )
        mentions, _ = price_mentions(self.text)
        self.add(
            "precio_lista",
            [
                (m.start, m.end, money(m.value))
                for m, mode in mentions
                if mode == "PRECIO_UNITARIO" and m.value is not None
            ],
        )
        has_quantity_context = bool(
            re.search(r"\b(?:stock|existencias|cantidad|cajas?|lotes?)\b", self.text, re.I)
        )
        if "precio_lista" not in self.result.fields:
            if not has_quantity_context:
                # Si no se declaró cantidad ni stock, un "total" dictado representa el importe del producto
                total_mentions = [
                    (m.start, m.end, money(m.value)) for m, mode in mentions if m.value is not None
                ]
                if total_mentions:
                    self.add("precio_lista", total_mentions)

        if "precio_lista" not in self.result.fields:
            moneda_cat = r"(?:bs\.?|bob|bolivianos?|bolivios?|d[oó]lares?|usd)"
            # Captura directa: "precio 4000", "precio de lista 5200", "precio de 5000", "total 3000" (sin contexto de cantidad)
            prefix = (
                r"\b(?:precio(?:\s+de\s+lista)?|valor|cuesta)\b"
                if has_quantity_context
                else r"\b(?:precio(?:\s+de\s+lista)?|total|valor|cuesta)\b"
            )
            for m in re.finditer(
                prefix
                + r"\s*[,;:]?\s*(?:(?:es\s+de|es|de)\s+)?(?:"
                + moneda_cat
                + r"\s*)?"
                + r"(?P<amount>"
                + AMOUNT
                + r")"
                + r"(?:\s*(?:"
                + moneda_cat
                + r"))?\b",
                self.text,
                re.I,
            ):
                if not _numero_es_medida_no_precio(self.text, m):
                    raw = m.group("amount").rstrip(".,")
                    val = monetary_amount(raw, decimal_from_text)
                    if val is not None and val > 0:
                        start = m.start("amount")
                        end = start + len(raw)
                        self.add("precio_lista", [(start, end, money(val))])
                        break
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

    def model(self):
        matches = []
        spoken_spans = {}
        # Read the complete explicit clause, not merely a decodable prefix.
        for cue in re.finditer(r"\b(?:modelo|c[oó]digo|cod)\b\s*:?\s*", self.text, re.I):
            start = cue.end()
            clause = re.split(
                r"[,.;\n]|\s+de(?=\s+(?:madera|metal|acero|malla|espuma|color|material)\b)|\s+\b(?:modelo|c[oó]digo|cod|con|marca|color|tipo|material|diseño|diseno|acabado|espesor|largo|ancho|precio|unidad|descripci[oó]n|observaciones|mejor|corrijo|perd[oó]n)\b|\s+o(?=\s+(?:modelo|c[oó]digo|cod)\b)",
                self.text[start:],
                maxsplit=1,
                flags=re.I,
            )[0].rstrip()
            status, value = _spoken_code_status(clause)
            if status == "NOT_CODE":
                # Ordinary model prose must not become fallback code warnings.
                if re.match(r"(?:a|de)\b", clause, re.I):
                    spoken_spans[start] = start + len(clause)
                continue
            if len(clause.split()) < 2:
                continue
            end = start + len(clause)
            spoken_spans[start] = end
            if value is not None:
                matches.append((start, end, value))
            else:
                self.result.warnings.append("modelo: código ambiguo; revise la transcripción.")
                self.result.evidence.append(
                    Candidate(
                        candidate_id=f"modelo-{start}-{end}",
                        label="modelo",
                        start=start,
                        end=end,
                        text=self.text[start:end],
                        source="RULE",
                        decision="UNRESOLVED",
                        reason="Código incompleto o ambiguo",
                    )
                )
        for m in re.finditer(
            r"\b(?:modelo|c[oó]digo|cod)\b\s*:?\s*"
            r"([A-Za-z0-9]+(?:\s*(?:-|gui[oó]n)\s*[A-Za-z0-9]+)*)",
            self.text,
            re.I,
        ):
            if m.start(1) in spoken_spans:
                continue
            raw = m.group(1)
            tail = self.text[m.end() :]
            continuation = re.match(
                r"\s+(?!(?:con|y|de|marca|color|tipo|material|diseno|diseño|acabado|espesor|largo|ancho|precio|unidad|descripcion|descripción|observaciones)\b)[\w-]+",
                tail,
                re.I,
            )
            if re.search(r"gui[oó]n", raw, re.I):
                normalized = re.sub(r"\s*gui[oó]n\s*", "-", raw, flags=re.I).strip()
                matches.append((m.start(1), m.end(1), normalized))
                continue
            if len(raw) < 2 or continuation:
                self.result.warnings.append("modelo: código ambiguo; revise la transcripción.")
                end = m.end() + (continuation.end() if continuation else 0)
                self.result.evidence.append(
                    Candidate(
                        candidate_id=f"modelo-{m.start(1)}-{end}",
                        label="modelo",
                        start=m.start(1),
                        end=end,
                        text=self.text[m.start(1) : end],
                        source="RULE",
                        decision="UNRESOLVED",
                        reason="Código incompleto o ambiguo",
                    )
                )
                continue
            matches.append((m.start(1), m.end(1), raw))
        if not matches and not re.search(r"\b(?:modelos?|c[oó]digo|cod)\b", self.text, re.I):
            # Require both letters and digits; never assemble a spoken code.
            for m in re.finditer(r"(?<![\w-])(?:[A-Z]{1,4}-?\d{2,6}[A-Za-z]?)(?![\w-])", self.text):
                matches.append((m.start(), m.end(), m.group()))
        self.add("modelo", matches)
        for candidate in self.result.evidence:
            if (
                candidate.label == "modelo"
                and candidate.start in spoken_spans
                and candidate.reason is None
            ):
                candidate.reason = "Equivalencia de código alfanumérico deletreado"

    def specific(self):
        pass


class ChairExtractor(Extractor):
    concepts = {**Extractor.concepts, "marca": "MARCA", "color_primario": "COLOR"}

    def catalogs(self):
        # Two literal active colors joined by "con" or "y" describe a combination.
        # Lists, alternatives and rectifications retain the shared ambiguity rules.
        colors = []
        for value in self.request.values:
            if value.concept == "COLOR":
                for alias in {value.name, value.code.replace("_", " "), *value.synonyms}:
                    for start, end in alias_matches(self.text, alias):
                        colors.append((start, end, value.id))
        colors = sorted(set(colors))
        if (
            len(colors) == 2
            and colors[0][2] != colors[1][2]
            and re.fullmatch(r"\s+(?:con|y)\s+", self.text[colors[0][1] : colors[1][0]], re.I)
            and not any(is_explicitly_negated(self.text, c[0]) for c in colors)
        ):
            self.add("color_primario", [colors[0]])
            self.add("color_secundario", [colors[1]])
            original = self.concepts
            self.concepts = {k: v for k, v in original.items() if k != "color_primario"}
            super().catalogs()
            self.concepts = original
        else:
            super().catalogs()

    def feature_context(self, name, start):
        # An explicit component in this match outranks a preceding component.
        # Bare material words still need the surrounding clause for association.
        if name == "material_respaldo" and re.match(
            r"(?:respaldo|espaldar)\b", self.text[start:], re.I
        ):
            return True
        prefix = re.split(r"[.;,\n]", self.text[max(0, start - 100) : start])[-1]
        parts = re.findall(r"\b(asiento|espaldar|respaldo)\b", prefix, re.I)
        if not parts:
            return True
        if name == "asiento":
            return parts[-1].lower() == "asiento"
        if name == "material_respaldo":
            return parts[-1].lower() != "asiento"
        return True

    def specific(self):
        self.model()
        specs = {}
        # These are physical features from HOMEX sources; no product identifiers.
        for name, pattern in {
            "apoyo_lumbar": r"apoyo lumbar|reposa lumbar|parte lumbar",
            "reposacabezas": r"reposa cabezas?|reposacabezas|reposa cabeza",
            "reposapies": r"reposa pi[eé]s|reposapi[eé]s",
            "brazos_regulables": r"(?:brazos|apoya ?brazos|reposa ?brazos)\s*(?:regulables?|ajustables?|acolchados?|ergon[oó]micos?)|apoyabrazos acolchados?",
            "material_respaldo": r"malla|(?:respaldo|espaldar)\s*(?:con|de|en)?\s*(?:malla|PVC|espuma(?:\s+de\s+alta\s+densidad)?|espuma)",
            "tapiz": r"cuero ecol[oó]gico|tela repelente a l[ií]quidos|(?:tapiz|tela) de alto tr[aá]fico",
            "asiento": r"(?:asiento\s+)?(?:espuma\s+(?:inyectada|de\s+alta\s+densidad)|esponja\s+de\s+alta\s+densidad|acolchado)|asiento acolchado",
            "suspension": r"(?:altura|ajuste|suspensi[oó]n|sistema)?\s*hidr[aá]ulic[ao]|pist[oó]n (?:clase\s+[1234]|a\s+gas)",
            "mecanismo": r"doble palanca|una palanca|sistema de rodilla|mecanismo sincr[oó]nico",
            "capacidad": r"\d+\s*kg",
            "patas": r"(?:[1-9]|cinco|cuatro)\s+patas(?: con ruedas)?",
            "giro": r"(?:360|370|trescientos\s+sesenta)\s*(?:grados|º|°)|giro(?:\s+de\s+\d+\s*grados|\s+completo)?",
            "base": r"base cromada|base (?:de |en )?PVC|base met[aá]lica de cromo grueso|patas cromadas|(?:base|patas)(?: de)? nylon de alta resistencia",
        }.items():
            self.add(
                "especificaciones." + name,
                [
                    (m.start(), m.end(), m.group())
                    for m in re.finditer(r"\b(?:" + pattern + r")\b", self.text, re.I)
                    if self.feature_context(name, m.start())
                ],
            )
            key = "especificaciones." + name
            if key in self.result.fields:
                specs[name] = self.result.fields.pop(key)
        if specs:
            self.result.fields["especificaciones"] = specs


def measure_number(raw):
    """Use existing cardinal/decimal parsers, with explicit spoken decimal separator."""
    parts = re.split(r"\s+(?:coma|punto)\s+", fold(raw))
    if len(parts) == 1:
        return decimal_from_text(raw) or (
            Decimal(n) if (n := cardinal(fold(raw).split())) is not None and n > 0 else None
        )
    if len(parts) != 2:
        return None
    whole, fraction = cardinal(parts[0].split()), cardinal(parts[1].split())
    if whole is None or fraction is None or not 0 < fraction < 100:
        return None
    return Decimal(f"{whole}.{fraction}")


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
        self.model()
        # A clause conjunction may precede a number, but cannot begin one.
        # Keep internal 'y' (treinta y dos) and full invalid tails for abstention.
        number = rf"(?:\d+(?:[,.]\d+)?|(?!\d|y\b){AMOUNT})(?:\s+(?:coma|punto)\s+(?:{AMOUNT}))?"
        for field, label in [
            ("espesor_mm", "espesor"),
            ("largo_mm", "largo"),
            ("ancho_mm", "ancho"),
        ]:
            matches = []
            patterns = [
                rf"\b{label}\s*(?:de|:)?\s*({number})\s*(mm|cm|mil[ií]metros?|cent[ií]metros?|metros?|m)\b"
            ]
            patterns.append(
                rf"(?<![\w.,−-])({number})\s*(mm|cm|mil[ií]metros?|cent[ií]metros?|metros?|m)\s+de {label}\b"
            )
            if field == "espesor_mm":
                # HDF board gauge is a thickness specification in this category.
                # Do not reinterpret an explicitly named other axis or a size pair.
                patterns.append(
                    rf"\bHDF\s*(?:de\s+)?({number})\s*(mm|mil[ií]metros?)\b"
                    r"(?!\s+(?:de\s+)?(?:ancho|largo|por|x)\b)"
                )
            for pattern in patterns:
                for m in re.finditer(pattern, self.text, re.I):
                    value = measure_number(m.group(1))
                    ambiguous_prefix = re.search(
                        r"(?:\b(?:o|menos)|[−-])\s*$", self.text[: m.start()], re.I
                    )
                    if value and not ambiguous_prefix:
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
                    rf"\b({number})\s*(?:m2|m²|metros cuadrados)\s+por caja\b",
                    self.text,
                    re.I,
                )
                if (value := measure_number(m.group(1))) is not None
            ],
        )


class OtherExtractor(Extractor):
    """Heterogeneous products use explicit name/description and real unit catalog."""


def extract_catalog(request: CatalogRequest) -> CatalogResult:
    # Category is supplied exclusively by the selected form, never inferred.
    return {"SILLA": ChairExtractor, "PISO_FLOTANTE": FloorExtractor, "OTRO": OtherExtractor}[
        request.category
    ](request).extract()
