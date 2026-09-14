"""Recursos JSON versionados incluidos en el wheel, cargados solo al solicitarlos."""

from importlib.resources import files
from typing import Literal

from pydantic import Field, model_validator

from homex_nlp.contracts.base import Axis, Contract, NonBlank


class FurnitureProfile(Contract):
    required_axes: list[Axis] = Field(default_factory=list)
    requires_thickness: bool = False
    requires_primary_color: bool = False


class FurnitureProfiles(Contract):
    schema_version: Literal["1.0"]
    profile_version: NonBlank
    status: Literal["UNCONFIGURED", "PROVIDED_BY_HOMEX"]
    profiles: dict[str, FurnitureProfile]

    @model_validator(mode="after")
    def supplied(self):
        if self.status == "UNCONFIGURED" and self.profiles:
            raise ValueError("Perfiles no proporcionados deben permanecer vacíos")
        return self


def load_furniture_profiles() -> FurnitureProfiles:
    raw = files(__package__).joinpath("furniture_profiles.json").read_text(encoding="utf-8")
    return FurnitureProfiles.model_validate_json(raw)
