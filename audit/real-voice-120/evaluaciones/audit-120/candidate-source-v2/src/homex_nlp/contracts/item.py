"""Propuesta singular; no es una fila comercial aprobada ni un producto maestro."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Literal

from pydantic import Field, model_validator

from homex_nlp.contracts.base import (
    Axis,
    Contract,
    Currency,
    DecimalText,
    LengthUnit,
    Money,
    NonBlank,
    PositiveDecimal,
    Quantity,
)


class Referenced(Contract):
    evidence_ids: list[NonBlank] = Field(default_factory=list)
    component_ref: NonBlank | None = None


class Component(Contract):
    component_id: NonBlank
    name: NonBlank
    evidence_ids: list[NonBlank] = Field(default_factory=list)


class Measurement(Referenced):
    value: PositiveDecimal
    unit: LengthUnit | None = None
    original_text: NonBlank
    value_mm: PositiveDecimal | None = None

    @model_validator(mode="after")
    def canonical(self):
        if self.value_mm is not None:
            factors = {"m": Decimal(1000), "cm": Decimal(10), "mm": Decimal(1)}
            if (
                self.unit is None
                or Decimal(self.value_mm) != Decimal(self.value) * factors[self.unit]
            ):
                raise ValueError("value_mm requiere unidad conocida y conversión exacta")
        return self


class Dimension(Measurement):
    axis: Axis | None = None


class Color(Referenced):
    value: NonBlank


class Accessory(Referenced):
    name: NonBlank
    quantity: Quantity | None = None


class NegotiatedPrice(Referenced):
    mode: Literal["TOTAL_NEGOCIADO"]
    stated_amount: Money
    currency: Currency
    line_total: Money
    unit_price_input: None = None
    unit_price_reference: DecimalText | None = None
    reference_is_approximate: bool = False
    origin: Literal["EXPLICIT_TOTAL", "HOMEX_DEFAULT_TOTAL"]

    @model_validator(mode="after")
    def authoritative(self):
        if self.line_total != self.stated_amount:
            raise ValueError("El total negociado debe conservarse exactamente")
        return self


class UnitPrice(Referenced):
    mode: Literal["PRECIO_UNITARIO"]
    stated_amount: Money
    currency: Currency
    unit_price_input: Money
    line_total: Money | None = None
    origin: Literal["EXPLICIT_UNIT"]

    @model_validator(mode="after")
    def authoritative(self):
        if self.stated_amount != self.unit_price_input:
            raise ValueError("El precio unitario debe coincidir con el importe dictado")
        return self


Price = Annotated[NegotiatedPrice | UnitPrice, Field(discriminator="mode")]


class ItemProposal(Contract):
    item_type: Literal["MUEBLE_MEDIDA"] = "MUEBLE_MEDIDA"
    name: NonBlank | None = None
    furniture_type_candidate: NonBlank | None = None
    quantity: Quantity | None = None
    components: list[Component] = Field(default_factory=list)
    dimensions: list[Dimension] = Field(default_factory=list)
    thicknesses: list[Measurement] = Field(default_factory=list)
    primary_color: Color | None = None
    secondary_color: Color | None = None
    accessories: list[Accessory] = Field(default_factory=list)
    price: Price | None = None
    observations: NonBlank | None = None
    unresolved: list[NonBlank] = Field(default_factory=list)  # IDs de candidatos pendientes.

    @model_validator(mode="after")
    def meaning_and_price(self):
        content = self.model_dump(exclude={"item_type"})
        if not any(v is not None and v != [] for v in content.values()):
            raise ValueError("Una propuesta vacía debe representarse como null")
        ids = [c.component_id for c in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("IDs de componente duplicados")
        if isinstance(self.price, UnitPrice):
            total = self.price.line_total
            if self.quantity is None and total is not None:
                raise ValueError("Sin cantidad no hay total derivable del unitario")
            if self.quantity is not None:
                expected = Decimal(self.price.unit_price_input) * self.quantity
                if total is None or Decimal(total) != expected:
                    raise ValueError("Total unitario incoherente con cantidad × unitario")
        if isinstance(self.price, NegotiatedPrice):
            reference = self.price.unit_price_reference
            if reference is None:
                if self.price.reference_is_approximate:
                    raise ValueError("No hay referencia que marcar aproximada")
            else:
                if self.quantity is None:
                    raise ValueError("Unitario referencial requiere cantidad")
                value = Decimal(reference)
                total = Decimal(self.price.line_total)
                quantum = Decimal(1).scaleb(value.as_tuple().exponent)
                expected = (total / self.quantity).quantize(quantum, rounding=ROUND_HALF_UP)
                if value != expected:
                    raise ValueError("Unitario referencial inconsistente")
                if self.price.reference_is_approximate != (value * self.quantity != total):
                    raise ValueError("Indicador aproximado incorrecto")
        return self
