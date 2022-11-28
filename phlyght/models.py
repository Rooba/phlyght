from typing import Any, Literal, Optional, Generic, TypeAlias, TypeVar
from uuid import UUID
from dataclasses import dataclass
from enum import Enum, auto

from pydantic import BaseModel, Field

__all__ = (
    "Archetype",
    "RoomType",
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

_T_M: TypeAlias = "Archetype | Room | Light | Scene | Zone | BridgeHome | GroupedLight | Device | Bridge | DevicePower | ZigbeeConnectivity | ZGPConnectivity | Motion | Temperature | LightLevel | Button | BehaviorScript | BehaviorInstance | GeofenceClient | Geolocation | EntertainmentConfiguration | Entertainment | Resource | Homekit"


_T = TypeVar("_T")


class RoomType(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    LIVING_ROOM = auto()
    KITCHEN = auto()
    DINING = auto()
    BEDROOM = auto()
    KIDS_BEDROOM = auto()
    BATHROOM = auto()
    NURSERY = auto()
    RECREATION = auto()
    OFFICE = auto()
    GYM = auto()
    HALLWAY = auto()
    TOILET = auto()
    FRONT_DOOR = auto()
    GARAGE = auto()
    TERRACE = auto()
    GARDEN = auto()
    DRIVEWAY = auto()
    CARPORT = auto()
    HOME = auto()
    DOWNSTAIRS = auto()
    UPSTAIRS = auto()
    TOP_FLOOR = auto()
    ATTIC = auto()
    GUEST_ROOM = auto()
    STAIRCASE = auto()
    LOUNGE = auto()
    MAN_CAVE = auto()
    COMPUTER = auto()
    STUDIO = auto()
    MUSIC = auto()
    TV = auto()
    READING = auto()
    CLOSET = auto()
    STORAGE = auto()
    LAUNDRY_ROOM = auto()
    BALCONY = auto()
    PORCH = auto()
    BARBECUE = auto()
    POOL = auto()
    OTHER = auto()


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


@dataclass
class _Dimming:
    brightness: float
    min_dim_level: Optional[float] = Field(0, repr=False)


@dataclass
class _XY:
    x: float
    y: float


@dataclass
class _On:
    on: bool = Field(..., alias="on")


@dataclass
class _ColorPoint:
    xy: _XY


@dataclass(frozen=True)
class _Identifier:
    rid: str
    rtype: str


@dataclass(frozen=True)
class _Metadata:
    name: str
    archetype: Optional[Archetype | RoomType] = Archetype.UNKNOWN_ARCHETYPE
    image: Optional[_Identifier] = Field(None, repr=False)


class _HueGroupedMeta(type):
    def update(cls):
        for v in cls.__dict__.values():
            if hasattr(v, "update_forward_refs"):
                v.update_forward_refs()


class _HueGrouped(metaclass=_HueGroupedMeta):
    ...


class _Lights(_HueGrouped):
    class ColorTemperature(BaseModel):
        mirek: Optional[int]
        mirek_valid: bool
        mirek_schema: dict[str, float]

    class Gamut(BaseModel):
        red: _XY
        green: _XY
        blue: _XY

    class Color(BaseModel):
        xy: _XY
        gamut: "_Lights.Gamut"
        gamut_type: Literal["A"] | Literal["B"] | Literal["C"]

    class Dynamics(BaseModel):
        status: str
        status_values: list[str]
        speed: float
        speed_valid: bool

    class Gradient(BaseModel):
        points: list[_ColorPoint]
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
        id_v1: Optional[str] = Field(
            ..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: _Identifier
        metadata: _Metadata
        on: _On = Field(repr=False)
        dimming: _Dimming
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


class _Scenes(_HueGrouped):
    class Action(BaseModel):
        on: Optional[_On]
        dimming: Optional[_Dimming]
        color: Optional[_ColorPoint]
        color_temperature: Optional[dict[str, float]]
        gradient: Optional[dict[str, list[_ColorPoint]]]
        effects: Optional[dict[str, str]]
        dynamics: Optional[dict[str, float]]

    class Actions(BaseModel):
        target: _Identifier
        action: "_Scenes.Action" = Field(repr=False)
        dimming: Optional[_Dimming]
        color: Optional[_ColorPoint]

    class PaletteColor(BaseModel):
        color: _ColorPoint
        dimming: _Dimming

    class PaletteTemperature(BaseModel):
        color_temperature: dict[str, float]
        dimming: _Dimming

    class Palette(BaseModel):
        color: list["_Scenes.PaletteColor"]
        dimming: Optional[list[_Dimming]]
        color_temperature: list["_Scenes.PaletteTemperature"]

    class Scene(BaseModel):
        id: UUID
        id_v1: Optional[str] = Field(
            ..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        metadata: _Metadata
        group: _Identifier
        actions: list["_Scenes.Actions"]
        palette: "_Scenes.Palette"
        speed: float
        auto_dynamic: bool
        type: Literal["scene"]


_Scenes.update()


class Room(BaseModel):
    type: Literal["room"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[_Identifier]
    metadata: _Metadata
    children: list[_Identifier]


class Zone(BaseModel):
    type: Literal["zone"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[_Identifier]
    metadata: _Metadata
    children: list[_Identifier]


class BridgeHome(BaseModel):
    type: Literal["bridge_home"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[_Identifier]
    children: list[_Identifier]


class GroupedLight(BaseModel):
    type: Literal["grouped_light"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    on: _On = Field(repr=False)
    alert: dict[str, list[str]]


class _ProductData(BaseModel):
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
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: list[_Identifier]
    metadata: _Metadata
    product_data: _ProductData


class Bridge(BaseModel):
    type: Literal["bridge"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    bridge_id: str
    time_zone: dict[str, str]


class _PowerState(BaseModel):
    battery_state: Literal["normal", "low", "critical"]
    battery_level: float = Field(le=100.0, ge=0.0)


class DevicePower(BaseModel):
    type: Literal["device_power"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    power_state: _PowerState


class ZigbeeConnectivity(BaseModel):
    type: Literal["zigbee_connectivity"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    status: Literal[
        "connected", "disconnected", "connectivity_issue", "unidirectional_incoming"
    ]
    mac_address: str


class ZGPConnectivity(BaseModel):
    type: Literal["zgp_connectivity"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    status: Literal[
        "connected", "disconnected", "connectivity_issue", "unidirectional_incoming"
    ]
    source_id: str


class Motion(BaseModel):
    type: Literal["motion"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    enabled: bool
    motion: dict[str, bool]


class _Temp(BaseModel):
    temperature: float = Field(lt=100.0, gt=-100.0)
    temperature_valid: bool


class Temperature(BaseModel):
    type: Literal["temperature"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    enabled: bool
    temperature: _Temp


class _Light(BaseModel):
    light_level: int
    light_level_valid: bool


class LightLevel(BaseModel):
    type: Literal["light_level"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    enabled: bool
    light: _Light


class Button(BaseModel):
    type: Literal["button"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
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


class BehaviorScript(BaseModel):
    type: Literal["behavior_script"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    description: str
    configuration_schema: dict[str, Any]
    trigger_schema: dict[str, Any]
    state_schema: dict[str, Any]
    version: str
    metadata: dict[str, str]


class _Dependee(BaseModel):
    type: str
    target: _Identifier
    level: str


class BehaviorInstance(BaseModel):
    type: Literal["behavior_instance"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    script_id: str
    enabled: bool
    state: Optional[dict[str, Any]]
    configuration: dict[str, Any]
    dependees: list[_Dependee]
    status: Literal["initializing", "running", "disabled", "errored"]
    last_error: str
    metadata: dict[Literal["name"], str]
    migrated_from: Optional[str] = None


class GeofenceClient(BaseModel):
    type: Literal["geofence_client"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    name: str


class Geolocation(BaseModel):
    type: Literal["geolocation"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    is_configured: bool = False


class _StreamProxy(BaseModel):
    mode: Literal["auto", "manual"]
    node: _Identifier


class _XYZ(BaseModel):
    x: float = Field(ge=-1.0, le=1.0)
    y: float = Field(ge=-1.0, le=1.0)
    z: float = Field(ge=-1.0, le=1.0)


class _SegmentRef(BaseModel):
    service: _Identifier
    index: int


class _EntertainmentChannel(BaseModel):
    channel_id: int = Field(ge=0, le=255)
    position: _XYZ
    members: list[_SegmentRef]


class _ServiceLocation(BaseModel):
    service: _Identifier
    position: _XYZ
    positions: list[_XYZ] = Field(max_items=2, min_items=1)


class _EntertainmentLocation(BaseModel):
    service_location: Optional[list[_ServiceLocation]] = []


class EntertainmentConfiguration(BaseModel):
    type: Literal["entertainment_configuration"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    metadata: dict[Literal["name"], str]
    name: Optional[str] = ""
    configuration_type: Literal["screen", "monitor", "music", "3dspace", "other"]
    status: Literal["active", "inactive"]
    active_streamer: Optional[_Identifier] = None
    stream_proxy: _StreamProxy
    channels: list[_EntertainmentChannel]
    locations: Optional[_EntertainmentLocation] = None
    light_services: list[_Identifier]


class _Segment(BaseModel):
    start: int = Field(..., ge=0)
    length: int = Field(..., ge=1)


class _SegmentManager(BaseModel):
    configurable: bool
    max_segments: int = Field(..., ge=1)
    segments: list[_Segment]


class Entertainment(BaseModel):
    type: Literal["entertainment"]
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: _Identifier
    renderer: bool
    proxy: bool
    max_streams: Optional[int] = Field(1, ge=1)
    segments: Optional[_SegmentManager] = None


class Homekit(BaseModel):
    id: UUID
    type: Optional[str]
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    status: Literal["paired", "pairing", "unpaired"]


class Resource(BaseModel):
    id: UUID
    type: Optional[str]
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")


Light = _Lights.Light
Scene = _Scenes.Scene
