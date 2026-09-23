"""Fachada determinística F03: una captura produce cero o una propuesta."""

from __future__ import annotations

from decimal import Decimal
from time import perf_counter

from homex_nlp.contracts import (
    Accessory,
    Dimension,
    ExtractionRequest,
    ExtractionResult,
    ItemProposal,
    Measurement,
    NegotiatedPrice,
    UnitPrice,
)
from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.result import EngineInfo
from homex_nlp.rules import (
    Match,
    find_accessories,
    find_measurements,
    find_price,
    find_products,
    find_quantity,
    find_thicknesses,
    money,
)


class RulesEngine:
    rules_version = "f03-rules-v1"

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        started = perf_counter()
        text = request.text
        candidates: list[Candidate] = []
        warnings: list[Warning] = [
            Warning(
                code="RULES_ONLY_MODE",
                path="",
                severity="INFO",
                message="Extracción determinística sin modelo NER.",
            )
        ]
        counter = 0

        def candidate(match: Match, decision: str = "ACCEPTED", reason: str | None = None) -> str:
            nonlocal counter
            counter += 1
            identifier = f"c{counter}"
            value = match.value
            if isinstance(value, Decimal):
                value = str(value)
            elif isinstance(value, tuple):
                value = [str(part) if isinstance(part, Decimal) else part for part in value]
            candidates.append(
                Candidate(
                    candidate_id=identifier,
                    label=match.label,
                    start=match.start,
                    end=match.end,
                    text=match.text,
                    source="RULE",
                    normalized_value=value,
                    decision=decision,
                    reason=reason,
                )
            )
            return identifier

        if not text.strip():
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="NO_PRODUCT",
                        path="",
                        severity="REVIEW",
                        message="No se dictó un producto.",
                    )
                ],
                started,
            )
        if "silla" in text.lower() or "piso" in text.lower():
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="OUT_OF_VOICE_SCOPE",
                        path="",
                        severity="REVIEW",
                        message="El catálogo no pertenece al alcance de muebles a medida v1.",
                    )
                ],
                started,
            )
        products = find_products(text)
        # Una rectificación explícita conserva evidencia rechazada y toma el último.
        if len(products) > 1 and " no " in f" {text.lower()} ":
            for product in products[:-1]:
                candidate(product, "REJECTED", "Rectificado explícitamente en el dictado")
            products = [products[-1]]
            warnings.append(
                Warning(
                    code="CONFLICTING_VALUES",
                    path="/item_proposal/name",
                    severity="REVIEW",
                    message="Se aplicó la rectificación explícita; revisar.",
                )
            )
        elif len(products) > 1:
            for product in products:
                candidate(product, "UNRESOLVED")
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="MULTIPLE_MAIN_PRODUCTS",
                        path="",
                        severity="REVIEW",
                        message="Se detectaron varios productos principales.",
                    )
                ],
                started,
            )
        if not products:
            return self._result(
                request,
                None,
                candidates,
                warnings
                + [
                    Warning(
                        code="NO_PRODUCT",
                        path="",
                        severity="REVIEW",
                        message="No se detectó un producto principal.",
                    )
                ],
                started,
            )
        candidate(products[0])
        quantity = find_quantity(text)
        if quantity:
            candidate(quantity)
        if quantity is None:
            warnings.append(
                Warning(
                    code="NO_QUANTITY",
                    path="/item_proposal/quantity",
                    severity="REVIEW",
                    message="Indique cantidad de muebles.",
                )
            )
        dimensions: list[Dimension] = []
        for axis in ("ancho", "alto", "profundidad"):
            for measurement in find_measurements(text, axis):
                evidence_id = candidate(measurement)
                value, raw_unit = measurement.value
                if raw_unit not in {"m", "mt", "mts", "metro", "metros", "cm", "mm"}:
                    warnings.append(
                        Warning(
                            code="MISSING_UNIT",
                            path="/item_proposal/dimensions",
                            severity="REVIEW",
                            message=f"La medida {measurement.text!r} no tiene unidad.",
                        )
                    )
                    unit = None
                    value_mm = None
                else:
                    unit = {"mt": "m", "mts": "m", "metro": "m", "metros": "m"}.get(
                        raw_unit, raw_unit
                    )
                    factor = {"m": Decimal(1000), "cm": Decimal(10), "mm": Decimal(1)}[unit]
                    value_mm = str(value * factor)
                dimensions.append(
                    Dimension(
                        axis=axis,
                        value=str(value),
                        unit=unit,
                        value_mm=value_mm,
                        original_text=measurement.text,
                        evidence_ids=[evidence_id],
                    )
                )
        thicknesses = []
        for thickness in find_thicknesses(text):
            evidence_id = candidate(thickness)
            value, unit = thickness.value
            thicknesses.append(
                Measurement(
                    value=str(value),
                    unit=unit,
                    value_mm=str(value),
                    original_text=thickness.text,
                    evidence_ids=[evidence_id],
                )
            )
        accessories = [
            Accessory(name=item.text, evidence_ids=[candidate(item)])
            for item in find_accessories(text)
        ]
        price_match, price_mode = find_price(text)
        price = None
        if price_mode == "INVALID_PRICE":
            warnings.append(
                Warning(
                    code="INVALID_PRICE",
                    path="/item_proposal/price",
                    severity="REVIEW",
                    message="El precio no tiene un formato válido completo.",
                )
            )
        elif price_match:
            price_id = candidate(price_match)
            amount = money(price_match.value)
            if price_mode == "PRECIO_UNITARIO":
                total = money(price_match.value * quantity.value) if quantity else None
                price = UnitPrice(
                    mode="PRECIO_UNITARIO",
                    stated_amount=amount,
                    unit_price_input=amount,
                    line_total=total,
                    currency=request.currency_context,
                    origin="EXPLICIT_UNIT",
                    evidence_ids=[price_id],
                )
            else:
                reference = None
                approximate = False
                if quantity:
                    quotient = price_match.value / quantity.value
                    reference = f"{quotient.quantize(Decimal('0.000001')):f}".rstrip("0").rstrip(
                        "."
                    )
                    approximate = Decimal(reference) * quantity.value != price_match.value
                price = NegotiatedPrice(
                    mode="TOTAL_NEGOCIADO",
                    stated_amount=amount,
                    line_total=amount,
                    currency=request.currency_context,
                    unit_price_reference=reference,
                    reference_is_approximate=approximate,
                    origin="EXPLICIT_TOTAL",
                    evidence_ids=[price_id],
                )
        item = ItemProposal(
            name=products[0].text,
            furniture_type_candidate=products[0].text.lower(),
            quantity=quantity.value if quantity else None,
            dimensions=dimensions,
            thicknesses=thicknesses,
            accessories=accessories,
            price=price,
        )
        return self._result(request, item, candidates, warnings, started)

    def _result(self, request, item, candidates, warnings, started):
        return ExtractionResult(
            request_id=request.request_id,
            status="REQUIRES_REVIEW" if item else "NO_PROPOSAL",
            text_original=request.text,
            item_proposal=item,
            proposed_item_count=int(item is not None),
            candidates=candidates,
            warnings=warnings,
            engine=EngineInfo(mode="RULES_ONLY", rules_version=self.rules_version),
            latency_nlp_ms=int((perf_counter() - started) * 1000),
        )
