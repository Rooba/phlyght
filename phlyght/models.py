from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel


class Lights:
    class MetaData(BaseModel):
        archetype: str
        name: str

    class Owner(BaseModel):
        rid: UUID
        rtype: str

    class On(BaseModel):
        on: bool

    class Dimming(BaseModel):
        brightness: float
        min_dim_level: float

    class MirekSchema(BaseModel):
        mirek_minimum: float
        mirek_maximum: float

    class ColorTemperature(BaseModel):
        mirek: Optional[int]
        mirek_valid: bool
        mirek_schema: "Lights.MirekSchema"

    class XY(BaseModel):
        x: float
        y: float

    class Gamut(BaseModel):
        red: "Lights.XY"
        green: "Lights.XY"
        blue: "Lights.XY"

    class Color(BaseModel):
        xy: "Lights.XY"
        gamut: "Lights.Gamut"
        gamut_type: Literal["A"] | Literal["B"] | Literal["C"]

    class Dynamics(BaseModel):
        status: str
        status_values: list[str]
        speed: float
        speed_valid: bool

    class Alert(BaseModel):
        action_values: list[str]

    class GradientColor(BaseModel):
        xy: "Lights.XY"

    class Gradient(BaseModel):
        points: list["Lights.GradientColor"]
        points_capable: int

    class Effects(BaseModel):
        effect: Optional[list[Literal["fire", "candle", "no_effect"]]]
        status_values: list[Literal["fire", "candle", "no_effect"]]
        status: Literal["fire", "candle", "no_effect"]
        effect_values: list[Literal["fire", "candle", "no_effect"]]

    class TimedEffects(BaseModel):
        effect: Literal["sunrise", "no_effect"]
        duration: int
        status_values: list[Literal["sunrise", "no_effect"]]
        status: Literal["sunrise", "no_effect"]
        effect_values: list[Literal["sunrise", "no_effect"]]

    class Light(BaseModel):
        id: UUID
        id_v1: str
        owner: "Lights.Owner"
        metadata: "Lights.MetaData"
        on: "Lights.On"
        dimming: "Lights.Dimming"
        dimming_delta: dict
        color_temperature: Optional["Lights.ColorTemperature"]
        color_temperature_delta: Optional[dict]
        color: Optional["Lights.Color"]
        gradient: Optional["Lights.Gradient"]
        dynamics: "Lights.Dynamics"
        alert: "Lights.Alert"
        signaling: dict
        mode: str
        effects: "Lights.Effects"
        type: str


for k in Lights.__dict__.values():
    if hasattr(k, "update_forward_refs"):
        k.update_forward_refs()
