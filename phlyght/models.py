__all__ = ("Room", "Light", "Scene")

from typing import Any, Literal, Optional, Generic, TypeVar
from uuid import UUID
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum, auto

_T = TypeVar("_T")


class Archetype(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    BRIDGE_V2 = auto()
    UNKNOWN_ARCHETYPE = auto()
    CLASSIC_BULB = auto()
    SULTAN_BULB = auto()
    FLOOD_BULB = auto()
    SPOT_BULB = auto()
    CANDLE_BULB = auto()
    LUSTER_BULB = auto()
    PENDANT_ROUND = auto()
    PENDANT_LONG = auto()
    CEILING_ROUND = auto()
    CEILING_SQUARE = auto()
    FLOOR_SHADE = auto()
    FLOOR_LANTERN = auto()
    TABLE_SHADE = auto()
    RECESSED_CEILING = auto()
    RECESSED_FLOOR = auto()
    SINGLE_SPOT = auto()
    DOUBLE_SPOT = auto()
    TABLE_WASH = auto()
    WALL_LANTERN = auto()
    WALL_SHADE = auto()
    FLEXIBLE_LAMP = auto()
    GROUND_SPOT = auto()
    WALL_SPOT = auto()
    PLUG = auto()
    HUE_GO = auto()
    HUE_LIGHTSTRIP = auto()
    HUE_IRIS = auto()
    HUE_BLOOM = auto()
    BOLLARD = auto()
    WALL_WASHER = auto()
    HUE_PLAY = auto()
    VINTAGE_BULB = auto()
    CHRISTMAS_TREE = auto()
    HUE_CENTRIS = auto()
    HUE_LIGHTSTRIP_TV = auto()
    HUE_TUBE = auto()
    HUE_SIGNE = auto()


class _id_v1(str):
    def __get__(self, instance, owner):
        return Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$)")


@dataclass
class Dimming:
    brightness: float
    min_dim_level: Optional[float] = Field(0, repr=False)


@dataclass
class XY:
    x: float
    y: float


@dataclass
class On:
    on: bool = Field(..., alias="on")


@dataclass
class ColorPoint:
    xy: XY


@dataclass(frozen=True)
class Identifier:
    rid: str
    rtype: str


@dataclass(frozen=True)
class Metadata:
    name: str
    archetype: Optional[Archetype] = Archetype.UNKNOWN_ARCHETYPE
    image: Optional[Identifier] = Field(None, repr=False)


class HueGroupedMeta(type):
    def update(cls):
        for v in cls.__dict__.values():
            if hasattr(v, "update_forward_refs"):
                v.update_forward_refs()


class HueGrouped(metaclass=HueGroupedMeta):
    ...


class _Lights(HueGrouped):
    class ColorTemperature(BaseModel):
        mirek: Optional[int]
        mirek_valid: bool
        mirek_schema: dict[str, float]

    class Gamut(BaseModel):
        red: XY
        green: XY
        blue: XY

    class Color(BaseModel):
        xy: XY
        gamut: "_Lights.Gamut"
        gamut_type: Literal["A"] | Literal["B"] | Literal["C"]

    class Dynamics(BaseModel):
        status: str
        status_values: list[str]
        speed: float
        speed_valid: bool

    class Gradient(BaseModel):
        points: list[ColorPoint]
        points_capable: int

    class Effects(BaseModel):
        effect: Optional[list[str]] = Field(repr=False)
        status_values: list[str] = Field(repr=False)
        status: str
        effect_values: list[str] = Field(repr=False)

    class TimedEffects(BaseModel):
        effect: str
        duration: int
        status_values: list[str] = Field(repr=False)
        status: str
        effect_values: list[str] = Field(repr=False)

    class Light(Generic[_T], BaseModel):
        id: UUID
        id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier
        metadata: Metadata
        on: On = Field(repr=False)
        dimming: Dimming
        dimming_delta: dict
        color_temperature: Optional["_Lights.ColorTemperature"]
        color_temperature_delta: Optional[dict]
        color: Optional["_Lights.Color"]
        gradient: Optional["_Lights.Gradient"]
        dynamics: "_Lights.Dynamics"
        alert: dict[str, list[str]]
        signaling: dict
        mode: str
        effects: "_Lights.Effects"
        type: Literal["light"]


_Lights.update()


class _Scenes(HueGrouped):
    class Action(BaseModel):
        on: Optional[On]
        dimming: Optional[Dimming]
        color: Optional[ColorPoint]
        color_temperature: Optional[dict[str, float]]
        gradient: Optional[dict[str, list[ColorPoint]]]
        effects: Optional[dict[str, str]]
        dynamics: Optional[dict[str, float]]

    class Actions(BaseModel):
        target: Identifier
        action: "_Scenes.Action" = Field(repr=False)
        dimming: Optional[Dimming]
        color: Optional[ColorPoint]

    class PaletteColor(BaseModel):
        color: ColorPoint
        dimming: Dimming

    class PaletteTemperature(BaseModel):
        color_temperature: dict[str, float]
        dimming: Dimming

    class Palette(BaseModel):
        color: list["_Scenes.PaletteColor"]
        dimming: Optional[list[Dimming]]
        color_temperature: list["_Scenes.PaletteTemperature"]

    class Scene(BaseModel):
        id: UUID
        id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        metadata: Metadata
        group: Identifier
        actions: list["_Scenes.Actions"]
        palette: "_Scenes.Palette"
        speed: float
        auto_dynamic: bool
        type: Literal["scene"]


_Scenes.update()


class Room(BaseModel):
    type: Literal["room"]
    id: UUID
    id_v1: _id_v1
    services: list[Identifier]
    metadata: Metadata
    children: list[Identifier]


class Zone(BaseModel):
    type: Literal["zone"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[Identifier]
    metadata: Metadata
    children: list[Identifier]


class BridgeHome(BaseModel):
    type: Literal["bridge_home"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[Identifier]
    children: list[Identifier]


class GroupedLight(BaseModel):
    type: Literal["grouped_light"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    on: On = Field(repr=False)
    alert: list[str]


class ProductData(BaseModel):
    model_id: str
    manufacturer_name: str
    product_name: str
    product_archetype: Archetype
    certified: bool
    software_version: Optional[str]
    hardware_platform_type: Optional[str]


class Device(BaseModel):
    type: Literal["device"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[Identifier]
    metadata: Metadata
    product_data: ProductData


class Bridge(BaseModel):
    type: Literal["bridge"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    bridge_id: str
    time_zone: dict[str, str]


class PowerState(BaseModel):
    battery_state: Literal["normal", "low", "critical"]
    battery_level: float = Field(lt=100.0, gt=0.0)


class DevicePower(BaseModel):
    type: Literal["device_power"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Identifier
    power_state: PowerState


class ZigbeeConnectivity(BaseModel):
    type: Literal["zigbee_connectivity"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Identifier
    status: Literal[
        "connected", "disconnected", "connectivity_issue", "unidirectional_incoming"
    ]
    mac_address: str


class ZGPConnectivity(BaseModel):
    type: Literal["zgp_connectivity"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Identifier
    status: Literal[
        "connected", "disconnected", "connectivity_issue", "unidirectional_incoming"
    ]
    source_id: str


class Motion(BaseModel):
    type: Literal["motion"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Identifier
    enabled: bool
    motion: dict[str, bool]


class _Temp(BaseModel):
    temperature: float = Field(lt=100.0, gt=-100.0)
    temperature_valid: bool


class Temperature(BaseModel):
    type: Literal["temperature"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Identifier
    enabled: bool
    temperature: _Temp


class _Light(BaseModel):
    light_level: int
    light_level_valid: bool


class LightLevel(BaseModel):
    type: Literal["light_level"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Identifier
    enabled: bool
    light: _Light


class Button(BaseModel):
    type: Literal["button"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Identifier
    metadata: dict[Literal["control_id"], int]
    button: dict[
        Literal["last_event"],
        Literal[
            "initial_press",
            "repeat",
            "short_release",
            "long_release",
            "double_short_release",
        ],
    ]


class BehaviorScript(BaseModel):
    type: Literal["behavior_script"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    description: str
    configuration_schema: dict[str, Any]
    trigger_schema: dict[str, Any]
    state_schema: dict[str, Any]
    version: str
    metadata: dict[str, str]


class Dependee(BaseModel):
    type: str
    target: Identifier
    level: str


class BehaviorInstance(BaseModel):
    type: Literal["behavior_instance"]
    id: UUID
    id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    script_id: str
    enabled: bool
    state: Optional[dict[str, Any]]
    configuration: dict[str, Any]
    dependees: list[Dependee]
    status: Literal["initializing", "running", "disabled", "errored"]
    last_error: str
    metadata: dict[Literal["name"], str]
    migrated_from: Optional[str] = None


class GeofenceClient(BaseModel):
    type: Literal["geofence_client"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    name: str


class Geolocation(BaseModel):
    type: Literal["geolocation"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    is_configured: bool = False


class StreamProxy(BaseModel):
    mode: Literal["auto", "manual"]
    node: Identifier


class EntertainmentConfiguration(BaseModel):
    type: Literal["entertainment_configuration"]
    id: UUID
    id_v1: str = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    metadata: dict[Literal["name"], str]
    name: Optional[str] = ""
    configuration_type: Literal["screen", "monitor", "music", "3dspace", "other"]
    status: Literal["active", "inactive"]
    active_streamer: Identifier
    stream_proxy: StreamProxy
    ...  # TODO: finish the last 4 objects


class Entertainment(BaseModel):
    ...


class Homekit(BaseModel):
    ...


class Resource(BaseModel):
    ...


Light = _Lights.Light
Scene = _Scenes.Scene
