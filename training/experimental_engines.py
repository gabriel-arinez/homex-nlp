"""Candidatos B/C offline: NER local y ensamblado conservador; sin promoción automática."""

import re
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from homex_nlp.contracts import ExtractionResult
from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.item import (
    Accessory,
    Component,
    Dimension,
    ItemProposal,
    Measurement,
    NegotiatedPrice,
    UnitPrice,
)
from homex_nlp.contracts.result import EngineInfo
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import NUMBER_WORDS, decimal_from_text, money


class NerExperimentalEngine:
    def __init__(self, model: Path):
        import spacy

        self.nlp = spacy.load(model)
        self.model_version = (
            "prf04-ner-" + sha256((model / "ner/model").read_bytes()).hexdigest()[:16]
        )

    def extract(self, request):
        text = request.text
        candidates = [
            Candidate(
                candidate_id=f"b{i}",
                label=e.label_,
                start=e.start_char,
                end=e.end_char,
                text=e.text,
                source="NER",
                decision="ACCEPTED",
            )
            for i, e in enumerate(self.nlp(text).ents, 1)
        ]
        warnings = []
        products = [c for c in candidates if c.label == "PRODUCTO"]
        if len(products) != 1:
            for c in candidates:
                c.decision = "UNRESOLVED"
            return self._result(
                request,
                None,
                candidates,
                [
                    Warning(
                        code="MULTIPLE_MAIN_PRODUCTS" if products else "NO_PRODUCT",
                        path="",
                        severity="REVIEW",
                        message="Indique un único mueble comercial.",
                    )
                ],
            )
        product = products[0]
        # El experimento conserva el alcance de voz aprobado.
        if re.search(r"\b(?:sillas?|pisos?)\b", product.text, re.I):
            return self._result(
                request,
                None,
                candidates,
                [
                    Warning(
                        code="OUT_OF_VOICE_SCOPE",
                        path="",
                        severity="REVIEW",
                        message="El producto queda fuera del alcance de voz.",
                    )
                ],
            )
        parts = [c for c in candidates if c.label == "COMPONENTE"]
        components = []
        scopes = []
        for i, c in enumerate(parts):
            c.component_ref = f"b-piece-{i + 1}"
            components.append(
                Component(component_id=c.component_ref, name=c.text, evidence_ids=[c.candidate_id])
            )
            end = parts[i + 1].start if i + 1 < len(parts) else len(text)
            boundary = re.search(
                r"[;.]|\b(?:Accesorios|Pedido|Cantidad|precio)\b", text[c.end : end], re.I
            )
            if boundary:
                end = c.end + boundary.start()
            scopes.append((c.end, end, c.component_ref))
        for c in candidates:
            if c.label in {"MATERIAL", "ESPESOR", "COLOR", "ACABADO", "CANTIDAD_INTERNA"}:
                c.component_ref = next(
                    (ref for start, end, ref in scopes if start <= c.start < end), None
                )
        quantities = [c for c in candidates if c.label == "CANTIDAD"]
        quantity = None
        if len(quantities) == 1:
            token = quantities[0].text.strip().lower()
            match = re.search(r"\b\d+\b", token)
            quantity = int(match.group()) if match else NUMBER_WORDS.get(token)
            if not quantity or quantity > 1000000:
                quantity = None
            quantities[0].normalized_value = quantity
        if quantity is None:
            warnings.append(
                Warning(
                    code="NO_QUANTITY",
                    path="/item_proposal/quantity",
                    severity="REVIEW",
                    message="Indique la cantidad comercial.",
                )
            )
        dimensions, thicknesses = [], []
        unresolved = []
        for c in candidates:
            if c.label in {"ALTO", "ANCHO", "PROFUNDIDAD", "LARGO", "DIAMETRO", "ESPESOR"}:
                match = re.fullmatch(r"\s*([\d.,]+)\s*(mm|cm|m)\s*", c.text, re.I)
                value = decimal_from_text(match[1]) if match else None
                if value is None:
                    c.decision = "UNRESOLVED"
                    unresolved.append(c.candidate_id)
                    continue
                unit = match[2].lower()
                data = dict(
                    value=str(value),
                    unit=unit,
                    original_text=c.text,
                    value_mm=str(value * {"m": 1000, "cm": 10, "mm": 1}[unit]),
                    component_ref=c.component_ref,
                    evidence_ids=[c.candidate_id],
                )
                if c.label == "ESPESOR":
                    thicknesses.append(Measurement(**data))
                else:
                    axis = c.label.lower()
                    pattern = {"diametro": "di[aá]metro"}.get(axis, axis)
                    before, after = text[max(0, c.start - 30) : c.start], text[c.end : c.end + 30]
                    explicit = re.search(pattern + r"\s*:?\s*$", before, re.I) or re.match(
                        r"\s*(?:de\s+)?" + pattern + r"\b", after, re.I
                    )
                    if explicit:
                        dimensions.append(Dimension(axis=axis, **data))
                    else:
                        c.decision = "UNRESOLVED"
                        unresolved.append(c.candidate_id)
                        warnings.append(
                            Warning(
                                code="MISSING_AXIS",
                                path="/item_proposal/dimensions",
                                severity="REVIEW",
                                message=f"Indique el eje de {c.text}.",
                            )
                        )
            if c.label == "UNIDAD_MEDIDA":
                normalized = c.text.strip().casefold()
                c.normalized_value = (
                    "JUEGO"
                    if re.fullmatch(r"juegos?", normalized)
                    else (
                        "PIEZA" if re.fullmatch(r"piezas?|pzas?\.?|unidades?", normalized) else None
                    )
                )
        price = None
        prices = [c for c in candidates if c.label == "PRECIO_UNITARIO"]
        if not prices:
            prices = [c for c in candidates if c.label == "PRECIO_TOTAL"]
        currency_conflict = (
            request.currency_context == "BOB"
            and re.search(r"\b(?:USD|d[oó]lares?)\b|\$", text, re.I)
            or request.currency_context == "USD"
            and re.search(r"\b(?:BOB|Bs|bolivianos?)\b", text, re.I)
        )
        if len(prices) == 1 and not currency_conflict:
            selected = prices[0]
            prefix = text[max(0, selected.start - 60) : selected.start]
            suffix = text[selected.end : selected.end + 30]
            explicit = (
                re.search(r"(?:precio|valor)\s+(?:unitario|por\s+unidad)", prefix, re.I)
                or re.match(
                    r"\s*(?:Bs|BOB|USD|bolivianos?|d[oó]lares?)?\s*(?:por\s+unidad|cada\s+uno|c/u)",
                    suffix,
                    re.I,
                )
                if selected.label == "PRECIO_UNITARIO"
                else re.search(r"total|importe", prefix, re.I)
            )
            if not explicit:
                selected.decision = "UNRESOLVED"
                unresolved.append(selected.candidate_id)
                prices = []
                warnings.append(
                    Warning(
                        code="INVALID_PRICE",
                        path="/item_proposal/price",
                        severity="REVIEW",
                        message="Indique si el importe es unitario o total.",
                    )
                )
        if len(prices) == 1 and not currency_conflict:
            c = prices[0]
            amount_match = re.search(r"[\d.,]+", c.text)
            amount = decimal_from_text(amount_match.group()) if amount_match else None
            if amount is not None:
                value = money(amount)
                c.normalized_value = value
                if c.label == "PRECIO_UNITARIO":
                    price = UnitPrice(
                        mode="PRECIO_UNITARIO",
                        stated_amount=value,
                        unit_price_input=value,
                        line_total=money(amount * quantity) if quantity else None,
                        currency=request.currency_context,
                        origin="EXPLICIT_UNIT",
                        evidence_ids=[c.candidate_id],
                    )
                else:
                    price = NegotiatedPrice(
                        mode="TOTAL_NEGOCIADO",
                        stated_amount=value,
                        line_total=value,
                        currency=request.currency_context,
                        origin="EXPLICIT_TOTAL",
                        evidence_ids=[c.candidate_id],
                    )
        elif currency_conflict:
            for c in prices:
                c.decision = "REJECTED"
                c.reason = "Moneda incompatible con la proforma."
            warnings.append(
                Warning(
                    code="UNSUPPORTED_CURRENCY",
                    path="/item_proposal/price",
                    severity="REVIEW",
                    message="Revise la moneda dictada.",
                )
            )
        item = ItemProposal(
            name=product.text,
            furniture_type_candidate=product.text,
            quantity=quantity,
            components=components,
            dimensions=dimensions,
            thicknesses=thicknesses,
            accessories=[
                Accessory(name=c.text, evidence_ids=[c.candidate_id])
                for c in candidates
                if c.label == "ACCESORIO" and c.decision == "ACCEPTED"
            ],
            price=price,
            unresolved=unresolved,
        )
        return self._result(request, item, candidates, warnings)

    def _result(self, request, item, candidates, warnings):
        return ExtractionResult(
            request_id=request.request_id,
            text_original=request.text,
            status="REQUIRES_REVIEW" if item else "NO_PROPOSAL",
            item_proposal=item,
            proposed_item_count=int(item is not None),
            candidates=candidates,
            warnings=warnings,
            engine=EngineInfo(
                mode="HYBRID",
                rules_version="prf04-ner-assembler-v1",
                model_version=self.model_version,
            ),
        )


class HybridExperimentalEngine:
    def __init__(self, ner: NerExperimentalEngine):
        self.ner = ner
        self.rules = RulesEngine()

    def extract(self, request):
        a, b = self.rules.extract(request), self.ner.extract(request)
        if a.status == "NO_PROPOSAL" and any(
            w.code in {"MULTIPLE_MAIN_PRODUCTS", "OUT_OF_VOICE_SCOPE"} for w in a.warnings
        ):
            a.engine = EngineInfo(
                mode="HYBRID",
                model_version=self.ner.model_version,
                rules_version="prf04-hybrid-experimental-v1",
            )
            # El NER se ejecutó; sus candidatos rechazados también quedan auditables.
            for c in b.candidates:
                c = c.model_copy(deep=True)
                c.component_ref = None
                c.decision = "REJECTED"
                c.reason = "La captura no contiene un único mueble comercial dentro del alcance."
                a.candidates.append(c)
            return ExtractionResult.model_validate(a.model_dump())
        if b.item_proposal is None:
            # Caída explícita: NER participó aunque no produjo propuesta utilizable.
            a.engine = EngineInfo(
                mode="HYBRID",
                model_version=self.ner.model_version,
                rules_version="prf04-hybrid-experimental-v1",
            )
            for c in b.candidates:
                c.component_ref = None
                a.candidates.append(c)
            return ExtractionResult.model_validate(a.model_dump())
        raw = deepcopy(b.model_dump())
        item = raw["item_proposal"]
        if a.item_proposal:
            original = a.item_proposal
            if original.quantity is not None:
                item["quantity"] = original.quantity
            # A conserva autoridad sobre precios cuando reconoce evidencia inequívoca.
            if original.price:
                price = original.price.model_dump(mode="json")
                price["evidence_ids"] = ["a-" + identifier for identifier in price["evidence_ids"]]
                if price["mode"] == "PRECIO_UNITARIO":
                    price["line_total"] = (
                        money(Decimal(price["unit_price_input"]) * item["quantity"])
                        if item["quantity"]
                        else None
                    )
                item["price"] = price
            elif item["price"] and item["price"]["mode"] == "PRECIO_UNITARIO":
                item["price"]["line_total"] = (
                    money(Decimal(item["price"]["unit_price_input"]) * item["quantity"])
                    if item["quantity"]
                    else None
                )
        for c in a.candidates:
            c = c.model_copy(deep=True)
            c.candidate_id = "a-" + c.candidate_id
            # No se asigna una pieza por posición al mezclar motores distintos.
            if c.component_ref:
                c.component_ref = None
                c.decision = "REJECTED"
                c.reason = "Relación del baseline conservada sólo como evidencia; requiere conciliación con NER."
            raw["candidates"].append(c.model_dump(mode="json"))
        raw["engine"] = {
            "mode": "HYBRID",
            "model_version": self.ner.model_version,
            "rules_version": "prf04-hybrid-experimental-v1",
            "normalization_version": "1.0",
        }
        if item["quantity"] is not None:
            raw["warnings"] = [w for w in raw["warnings"] if w["code"] != "NO_QUANTITY"]
        return ExtractionResult.model_validate(raw)
