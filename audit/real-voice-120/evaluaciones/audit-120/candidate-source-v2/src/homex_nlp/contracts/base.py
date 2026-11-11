"""Tipos de transporte estrictos: sin coerciones monetarias o cantidades ficticias."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_default=True)


NonBlank = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
Quantity = Annotated[int, Field(strict=True, ge=1, le=2_147_483_647)]
Count = Annotated[int, Field(strict=True, ge=0)]
Currency = Literal["BOB", "USD"]
Axis = Literal["ancho", "alto", "profundidad", "largo", "diametro"]
LengthUnit = Literal["m", "cm", "mm"]
# Importes NUMERIC(14,2); el backend valida límites comerciales más específicos.
Money = Annotated[str, StringConstraints(pattern=r"^(0|[1-9][0-9]{0,11})\.[0-9]{2}$")]
DecimalText = Annotated[str, StringConstraints(pattern=r"^(0|[1-9][0-9]{0,11})(\.[0-9]{1,12})?$")]


def positive(value: str) -> str:
    if Decimal(value) <= 0:
        raise ValueError("La medida debe ser positiva")
    return value


PositiveDecimal = Annotated[DecimalText, AfterValidator(positive)]
Ratio = Annotated[str, StringConstraints(pattern=r"^(0(\.[0-9]{1,12})?|1(\.0{1,12})?)$")]
