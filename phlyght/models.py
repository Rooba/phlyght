from typing import (
    Any as _Any,
    Literal,
    Optional as _Optional,
    Generic as _Generic,
    TypeAlias as _TypeAlias,
    TypeVar as _TypeVar,
)
from uuid import UUID as _UUID
from dataclasses import dataclass as _dataclass
from enum import Enum as _Enum, auto as _auto

from pydantic import BaseModel as _BaseModel, Field as _Field

__all__ = (
    "_Archetype",
    "_RoomType",
    "Room",
    "Light",
    "Scene",
    "Zone",
    "BridgeHome",
    "GroupedLight",
    "Device",
    "Bridge",
    "DevicePower",
    "ZigbeeConnectivity",
    "ZGPConnectivity",
    "Motion",
    "Temperature",
    "LightLevel",
    "Button",
    "BehaviorScript",
    "BehaviorInstance",
    "GeofenceClient",
    "Geolocation",
    "EntertainmentConfiguration",
    "Entertainment",
    "Resource",
    "Homekit",
)

_T_M: _TypeAlias = "_RoomType | _Archetype | Room | Light | Scene | Zone | BridgeHome | GroupedLight | Device | Bridge | DevicePower | ZigbeeConnectivity | ZGPConnectivity | Motion | Temperature | LightLevel | Button | BehaviorScript | BehaviorInstance | GeofenceClient | Geolocation | EntertainmentConfiguration | Entertainment | Resource | Homekit"


_T = _TypeVar("_T")


class _RoomType(_Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    LIVING_ROOM = _auto()
    KITCHEN = _auto()
    DINING = _auto()
    BEDROOM = _auto()
    KIDS_BEDROOM = _auto()
    BATHROOM = _auto()
    NURSERY = _auto()
    RECREATION = _auto()
    OFFICE = _auto()
    GYM = _auto()
    HALLWAY = _auto()
    TOILET = _auto()
    FRONT_DOOR = _auto()
    GARAGE = _auto()
    TERRACE = _auto()
    GARDEN = _auto()
    DRIVEWAY = _auto()
    CARPORT = _auto()
    HOME = _auto()
    DOWNSTAIRS = _auto()
    UPSTAIRS = _auto()
    TOP_FLOOR = _auto()
    ATTIC = _auto()
    GUEST_ROOM = _auto()
    STAIRCASE = _auto()
    LOUNGE = _auto()
    MAN_CAVE = _auto()
    COMPUTER = _auto()
    STUDIO = _auto()
    MUSIC = _auto()
    TV = _auto()
    READING = _auto()
    CLOSET = _auto()
    STORAGE = _auto()
    LAUNDRY_ROOM = _auto()
    BALCONY = _auto()
    PORCH = _auto()
    BARBECUE = _auto()
    POOL = _auto()
    OTHER = _auto()


class _Archetype(_Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    BRIDGE_V2 = _auto()
    UNKNOWN_ARCHETYPE = _auto()
    CLASSIC_BULB = _auto()
    SULTAN_BULB = _auto()
    FLOOD_BULB = _auto()
    SPOT_BULB = _auto()
    CANDLE_BULB = _auto()
    LUSTER_BULB = _auto()
    PENDANT_ROUND = _auto()
    PENDANT_LONG = _auto()
    CEILING_ROUND = _auto()
    CEILING_SQUARE = _auto()
    FLOOR_SHADE = _auto()
    FLOOR_LANTERN = _auto()
    TABLE_SHADE = _auto()
    RECESSED_CEILING = _auto()
    RECESSED_FLOOR = _auto()
    SINGLE_SPOT = _auto()
    DOUBLE_SPOT = _auto()
    TABLE_WASH = _auto()
    WALL_LANTERN = _auto()
    WALL_SHADE = _auto()
    FLEXIBLE_LAMP = _auto()
    GROUND_SPOT = _auto()
    WALL_SPOT = _auto()
    PLUG = _auto()
    HUE_GO = _auto()
    HUE_LIGHTSTRIP = _auto()
    HUE_IRIS = _auto()
    HUE_BLOOM = _auto()
    BOLLARD = _auto()
    WALL_WASHER = _auto()
    HUE_PLAY = _auto()
    VINTAGE_BULB = _auto()
    CHRISTMAS_TREE = _auto()
    HUE_CENTRIS = _auto()
    HUE_LIGHTSTRIP_TV = _auto()
    HUE_TUBE = _auto()
    HUE_SIGNE = _auto()


@_dataclass
class _Dimming:
    brightness: float
    min_dim_level: _Optional[float] = _Field(0, repr=False)


@_dataclass
class _XY:
    x: float
    y: float


@_dataclass
class _On:
    on: bool = _Field(..., alias="on")


@_dataclass
class _ColorPoint:
    xy: _XY


@_dataclass(frozen=True)
class _Identifier:
    rid: str
    rtype: str


@_dataclass(frozen=True)
class _Metadata:
    name: str
    archetype: _Optional[_Archetype | _RoomType] = _Archetype.UNKNOWN_ARCHETYPE
    image: _Optional[_Identifier] = _Field(None, repr=False)


class _HueGroupedMeta(type):
    def update(cls):
        for v in cls.__dict__.values():
            if hasattr(v, "update_forward_refs"):
                v.update_forward_refs()


class _HueGrouped(metaclass=_HueGroupedMeta):
    ...


class _Lights(_HueGrouped):
    class ColorTemperature(_BaseModel):
        mirek: _Optional[int]
        mirek_valid: bool
        mirek_schema: dict[str, float]

    class Gamut(_BaseModel):
        red: _XY
        green: _XY
        blue: _XY

    class Color(_BaseModel):
        xy: _XY = _Field(None)
        gamut: "_Lights.Gamut" = _Field(None)
        gamut_type: Literal["A", "B", "C"] = _Field(None)

    class Dynamics(_BaseModel):
        status: str = _Field(None)
        status_values: list[str] = _Field(None)
        speed: float = _Field(None)
        speed_valid: bool = _Field(None)

    class Gradient(_BaseModel):
        points: list[_ColorPoint] = _Field([])
        points_capable: int = _Field(0)

    class Effects(_BaseModel):
        effect: _Optional[list[str]] = _Field(repr=False)
        status_values: list[str] = _Field(repr=False)
        status: str = _Field("")
        effect_values: list[str] = _Field(repr=False)

    class TimedEffects(_BaseModel):
        effect: str = _Field("")
        duration: int = _Field(0)
        status_values: list[str] = _Field(repr=False)
        status: str = _Field("")
        effect_values: list[str] = _Field(repr=False)

    class Light(_Generic[_T], _BaseModel):
        id: _UUID
        id_v1: _Optional[str] = _Field(
            ..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: _Optional[_Identifier]
        metadata: _Optional[_Metadata]
        on: _Optional[_On] = _Field(repr=False)
        dimming: _Optional[_Dimming]
        dimming_delta: _Optional[dict]
        color_temperature: _Optional["_Lights.ColorTemperature"]
        color_temperature_delta: _Optional[dict]
        color: _Optional["_Lights.Color"]
        gradient: _Optional["_Lights.Gradient"]
        dynamics: _Optional["_Lights.Dynamics"]
        alert: _Optional[dict[str, list[str]]]
        signaling: _Optional[dict]
        mode: _Optional[str]
        effects: _Optional["_Lights.Effects"]
        type: Literal["light"] = "light"


_Lights.update()


class _Scenes(_HueGrouped):
    class Action(_BaseModel):
        on: _Optional[_On]
        dimming: _Optional[_Dimming]
        color: _Optional[_ColorPoint]
        color_temperature: _Optional[dict[str, float]]
        gradient: _Optional[dict[str, list[_ColorPoint]]]
        effects: _Optional[dict[str, str]]
        dynamics: _Optional[dict[str, float]]

    class Actions(_BaseModel):
        target: _Identifier
        action: "_Scenes.Action" = _Field(repr=False)
        dimming: _Optional[_Dimming]
        color: _Optional[_ColorPoint]

    class PaletteColor(_BaseModel):
        color: _ColorPoint
        dimming: _Dimming

    class PaletteTemperature(_BaseModel):
        color_temperature: dict[str, float]
        dimming: _Dimming

    class Palette(_BaseModel):
        color: list["_Scenes.PaletteColor"]
        dimming: _Optional[list[_Dimming]]
        color_temperature: list["_Scenes.PaletteTemperature"]

    class Scene(_BaseModel):
        id: _UUID
        id_v1: _Optional[str] = _Field(
            ..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        metadata: _Metadata
        group: _Identifier
        actions: list["_Scenes.Actions"]
        palette: "_Scenes.Palette"
        speed: float
        auto_dynamic: bool
        type: Literal["scene"] = "scene"


_Scenes.update()


class Room(_BaseModel):
    type: Literal["room"] = "room"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[_Identifier]
    metadata: _Metadata
    children: list[_Identifier]


class Zone(_BaseModel):
    type: Literal["zone"] = "zone"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[_Identifier]
    metadata: _Metadata
    children: list[_Identifier]


class BridgeHome(_BaseModel):
    type: Literal["bridge_home"] = "bridge_home"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[_Identifier]
    children: list[_Identifier]


class GroupedLight(_BaseModel):
    type: Literal["grouped_light"] = "grouped_light"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    on: _On = _Field(repr=False)
    alert: dict[str, list[str]]


class _ProductData(_BaseModel):
    model_id: str
    manufacturer_name: str
    product_name: str
    product_archetype: _Archetype
    certified: bool
    software_version: _Optional[str]
    hardware_platform_type: _Optional[str]


class Device(_BaseModel):
    type: Literal["device"] = "device"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[_Identifier]
    metadata: _Metadata
    product_data: _ProductData


class Bridge(_BaseModel):
    type: Literal["bridge"] = "bridge"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    bridge_id: str
    time_zone: dict[str, str]


class _PowerState(_BaseModel):
    battery_state: Literal["normal", "low", "critical"]
    battery_level: float = _Field(le=100.0, ge=0.0)


class DevicePower(_BaseModel):
    type: Literal["device_power"] = "device_power"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    power_state: _PowerState


class ZigbeeConnectivity(_BaseModel):
    type: Literal["zigbee_connectivity"] = "zigbee_connectivity"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    status: Literal[
        "connected", "disconnected", "connectivity_issue", "unidirectional_incoming"
    ]
    mac_address: str


class ZGPConnectivity(_BaseModel):
    type: Literal["zgp_connectivity"] = "zgp_connectivity"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    status: Literal[
        "connected", "disconnected", "connectivity_issue", "unidirectional_incoming"
    ]
    source_id: str


class Motion(_BaseModel):
    type: Literal["motion"] = "motion"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    enabled: bool
    motion: dict[str, bool]


class _Temp(_BaseModel):
    temperature: float = _Field(lt=100.0, gt=-100.0)
    temperature_valid: bool


class Temperature(_BaseModel):
    type: Literal["temperature"] = "temperature"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    enabled: _Optional[bool]
    temperature: _Temp


class _Light(_BaseModel):
    light_level: _Optional[int]
    light_level_valid: _Optional[bool]


class LightLevel(_BaseModel):
    type: Literal["light_level"] = "light_level"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Optional[_Identifier]
    enabled: _Optional[bool]
    light: _Optional[_Light]


class Button(_BaseModel):
    type: Literal["button"] = "button"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
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


class BehaviorScript(_BaseModel):
    type: Literal["behavior_script"] = "behavior_script"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    description: str
    configuration_schema: dict[str, _Any]
    trigger_schema: dict[str, _Any]
    state_schema: dict[str, _Any]
    version: str
    metadata: dict[str, str]


class _Dependee(_BaseModel):
    type: str
    target: _Identifier
    level: str


class BehaviorInstance(_BaseModel):
    type: Literal["behavior_instance"] = "behavior_instance"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    script_id: str
    enabled: bool
    state: _Optional[dict[str, _Any]]
    configuration: dict[str, _Any]
    dependees: list[_Dependee]
    status: Literal["initializing", "running", "disabled", "errored"]
    last_error: str
    metadata: dict[Literal["name"], str]
    migrated_from: _Optional[str] = None


class GeofenceClient(_BaseModel):
    type: Literal["geofence_client"] = "geofence_client"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    name: str


class Geolocation(_BaseModel):
    type: Literal["geolocation"] = "geolocation"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    is_configured: bool = False


class _StreamProxy(_BaseModel):
    mode: Literal["auto", "manual"]
    node: _Identifier


class _XYZ(_BaseModel):
    x: float = _Field(ge=-1.0, le=1.0)
    y: float = _Field(ge=-1.0, le=1.0)
    z: float = _Field(ge=-1.0, le=1.0)


class _SegmentRef(_BaseModel):
    service: _Identifier
    index: int


class _EntertainmentChannel(_BaseModel):
    channel_id: int = _Field(ge=0, le=255)
    position: _XYZ
    members: list[_SegmentRef]


class _ServiceLocation(_BaseModel):
    service: _Identifier
    position: _XYZ
    positions: list[_XYZ] = _Field(max_items=2, min_items=1)


class _EntertainmentLocation(_BaseModel):
    service_location: _Optional[list[_ServiceLocation]] = []


class EntertainmentConfiguration(_BaseModel):
    type: Literal["entertainment_configuration"] = "entertainment_configuration"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    metadata: dict[Literal["name"], str]
    name: _Optional[str] = ""
    configuration_type: Literal["screen", "monitor", "music", "3dspace", "other"]
    status: Literal["active", "inactive"]
    active_streamer: _Optional[_Identifier] = None
    stream_proxy: _StreamProxy
    channels: list[_EntertainmentChannel]
    locations: _Optional[_EntertainmentLocation] = None
    light_services: list[_Identifier]


class _Segment(_BaseModel):
    start: int = _Field(..., ge=0)
    length: int = _Field(..., ge=1)


class _SegmentManager(_BaseModel):
    configurable: bool
    max_segments: int = _Field(..., ge=1)
    segments: list[_Segment]


class Entertainment(_BaseModel):
    type: Literal["entertainment"] = "entertainment"
    id: _UUID
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    renderer: bool
    proxy: bool
    max_streams: _Optional[int] = _Field(1, ge=1)
    segments: _Optional[_SegmentManager] = None


class Homekit(_BaseModel):
    id: _UUID
    type: _Optional[str] = "resource"
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    status: Literal["paired", "pairing", "unpaired"]


class Resource(_BaseModel):
    id: _UUID
    type: _Optional[str] = "device"
    id_v1: _Optional[str] = _Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")


Light = _Lights.Light
Scene = _Scenes.Scene
