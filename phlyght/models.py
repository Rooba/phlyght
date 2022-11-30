from typing import Any, Literal, Optional, TypeAlias, TypeVar
from uuid import UUID
from enum import Enum, auto

from pydantic import BaseModel, Field

try:
    from ujson import loads, dumps  # type: ignore
except ImportError:
    from orjson import loads, dumps  # type: ignore
except ImportError:  # type: ignore
    from json import loads, dumps  # noqa


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

_T_M: TypeAlias = "RoomType | Archetype | Room | Light | Scene | Zone | BridgeHome | GroupedLight | Device | Bridge | DevicePower | ZigbeeConnectivity | ZGPConnectivity | Motion | Temperature | LightLevel | Button | BehaviorScript | BehaviorInstance | GeofenceClient | Geolocation | EntertainmentConfiguration | Entertainment | Resource | Homekit"


_T = TypeVar("_T")


class Entity(BaseModel):
    __module__ = "phlyght"
    __cache__: dict[str, type] = {}
    id: UUID = Field(description="The unique identifier of the entity.")

    class Config:
        __root__: Optional["Entity"]
        json_loads = loads
        json_dumps = dumps

    @classmethod
    def get_entities(cls) -> dict[str, type]:
        return cls.__cache__

    @classmethod
    def __prepare__(cls, name, bases, **kwds):
        return super().__prepare__(name, bases, **kwds)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        Entity.__cache__[
            _.get_default() if (_ := cls.__fields__.get("type")) else "unknown"
        ] = cls

    def __hash__(self) -> int:
        return hash(self.id)


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


class Dimming(BaseModel):
    class Config:
        frozen = True
        allow_mutation = False
        validate_assignment = True

    brightness: Optional[float]
    min_dim_level: Optional[float] = Field(0, repr=False)


class XY(BaseModel):
    class Config:
        frozen = True
        allow_mutation = False
        validate_assignment = True

    x: Optional[float]
    y: Optional[float]


class On(BaseModel):
    class Config:
        frozen = True
        allow_mutation = False
        validate_assignment = True

    on: bool = Field(..., alias="on")


class ColorPoint(BaseModel):
    xy: Optional[XY]


class Identifier(BaseModel):
    class Config:
        frozen = True
        allow_mutation = False
        validate_assignment = True

    rid: Optional[str]
    rtype: Optional[str]


class Metadata(BaseModel):
    class Config:
        frozen = True
        allow_mutation = False
        validate_assignment = True

    name: Optional[str]
    archetype: Optional[Archetype | RoomType] = Archetype.UNKNOWN_ARCHETYPE
    image: Optional[Identifier] = Field(None, repr=False)


class ColorTemperature(BaseModel):
    mirek: Optional[int]
    mirek_valid: Optional[bool]
    mirek_schema: Optional[dict[str, float]]


class Gamut(BaseModel):
    red: Optional[XY]
    green: Optional[XY]
    blue: Optional[XY]


class Color(BaseModel):
    xy: Optional[XY]
    gamut: Optional["Gamut"]
    gamut_type: Optional[Literal["A", "B", "C"]]


class Dynamics(BaseModel):
    status: Optional[str]
    status_values: Optional[list[str]]
    speed: Optional[float]
    speed_valid: Optional[bool]


class Gradient(BaseModel):
    points: Optional[list[ColorPoint]]
    points_capable: Optional[int]


class Effects(BaseModel):
    effect: Optional[list[str]]
    status_values: Optional[list[str]]
    status: Optional[str]
    effect_values: Optional[list[str]]


class TimedEffects(BaseModel):
    effect: Optional[str]
    duration: Optional[int]
    status_values: Optional[list[str]]
    status: Optional[str]
    effect_values: Optional[list[str]]


class Action(BaseModel):
    on: Optional[On]
    dimming: Optional[Dimming]
    color: Optional[ColorPoint]
    color_temperature: Optional[dict[str, float]]
    gradient: Optional[dict[str, list[ColorPoint]]]
    effects: Optional[dict[str, str]]
    dynamics: Optional[dict[str, float]]


class Actions(BaseModel):
    target: Optional[Identifier]
    action: Optional[Action]
    dimming: Optional[Dimming]
    color: Optional[ColorPoint]


class PaletteColor(BaseModel):
    color: Optional[ColorPoint]
    dimming: Optional[Dimming]


class PaletteTemperature(BaseModel):
    color_temperature: dict[str, float]
    dimming: Optional[Dimming]


class Palette(BaseModel):
    color: Optional[list[PaletteColor]]
    dimming: Optional[list[Dimming]]
    color_temperature: Optional[list[PaletteTemperature]]


class ProductData(BaseModel):
    model_id: Optional[str]
    manufacturer_name: Optional[str]
    product_name: Optional[str]
    product_archetype: Optional[Archetype]
    certified: Optional[bool]
    software_version: Optional[str]
    hardware_platform_type: Optional[str]


class PowerState(BaseModel):
    battery_state: Literal["normal", "low", "critical"]
    battery_level: float = Field(le=100.0, ge=0.0)


class Temp(BaseModel):
    temperature: float = Field(lt=100.0, gt=-100.0)
    temperature_valid: Optional[bool]


class LightLevelValue(BaseModel):
    light_level: Optional[int]
    light_level_valid: Optional[bool]


class StreamProxy(BaseModel):
    mode: Literal["auto", "manual"]
    node: Optional[Identifier]


class XYZ(BaseModel):
    x: float = Field(ge=-1.0, le=1.0)
    y: float = Field(ge=-1.0, le=1.0)
    z: float = Field(ge=-1.0, le=1.0)


class SegmentRef(BaseModel):
    service: Optional[Identifier]
    index: Optional[int]


class EntertainmentChannel(BaseModel):
    channel_id: int = Field(ge=0, le=255)
    position: Optional[XYZ]
    members: Optional[list[SegmentRef]]


class ServiceLocation(BaseModel):
    service: Optional[Identifier]
    position: Optional[XYZ]
    positions: list[XYZ] = Field(max_items=2, min_items=1)


class EntertainmentLocation(BaseModel):
    service_location: Optional[list[ServiceLocation]]


class Segment(BaseModel):
    start: int = Field(..., ge=0)
    length: int = Field(..., ge=1)


class SegmentManager(BaseModel):
    configurable: Optional[bool]
    max_segments: int = Field(..., ge=1)
    segments: Optional[list[Segment]]


class Dependee(BaseModel):
    type: Optional[str]
    target: Optional[Identifier]
    level: Optional[str]


class BehaviorInstance(Entity):
    type: Literal["behavior_instance"] = "behavior_instance"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    script_id: Optional[str]
    enabled: Optional[bool]
    state: Optional[dict[str, Any]]
    configuration: dict[str, Any]
    dependees: Optional[list[Dependee]]
    status: Literal["initializing", "running", "disabled", "errored"]
    last_error: Optional[str]
    metadata: dict[Literal["name"], str]
    migrated_from: Optional[str] = None


class BehaviorScript(Entity):
    type: Literal["behavior_script"] = "behavior_script"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    description: Optional[str]
    configuration_schema: dict[str, Any]
    trigger_schema: dict[str, Any]
    state_schema: dict[str, Any]
    version: Optional[str]
    metadata: dict[str, str]


class Bridge(Entity):
    type: Literal["bridge"] = "bridge"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    bridge_id: Optional[str]
    time_zone: dict[str, str]


class BridgeHome(Entity):
    type: Literal["bridge_home"] = "bridge_home"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: Optional[list[Identifier]]
    children: Optional[list[Identifier]]


class Button(Entity):
    type: Literal["button"] = "button"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    metadata: dict[Literal["control_id"], int]
    button: Optional[
        dict[
            Literal["last_event"],
            Literal[
                "initial_press",
                "repeat",
                "short_release",
                "long_release",
                "double_short_release",
            ],
        ]
    ]


class Device(Entity):
    type: Literal["device"] = "device"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: Optional[list[Identifier]]
    metadata: Optional[Metadata]
    product_data: Optional[ProductData]


class DevicePower(Entity):
    type: Literal["device_power"] = "device_power"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    power_state: Optional[PowerState]


class Entertainment(Entity):
    type: Literal["entertainment"] = "entertainment"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    renderer: Optional[bool]
    proxy: Optional[bool]
    max_streams: Optional[int] = Field(1, ge=1)
    segments: Optional[SegmentManager] = None


class EntertainmentConfiguration(Entity):
    type: Literal["entertainment_configuration"] = "entertainment_configuration"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    metadata: dict[Literal["name"], str]
    name: Optional[str] = ""
    configuration_type: Literal["screen", "monitor", "music", "3dspace", "other"]
    status: Literal["active", "inactive"]
    active_streamer: Optional[Identifier] = None
    stream_proxy: Optional[StreamProxy]
    channels: Optional[list[EntertainmentChannel]]
    locations: Optional[EntertainmentLocation] = None
    light_services: Optional[list[Identifier]]


class GeofenceClient(Entity):
    type: Literal["geofence_client"] = "geofence_client"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    name: Optional[str]


class Geolocation(Entity):
    type: Literal["geolocation"] = "geolocation"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    is_configured: Optional[bool] = False


class GroupedLight(Entity):
    type: Literal["grouped_light"] = "grouped_light"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    on: On = Field(repr=False)
    alert: dict[str, list[str]]


class Homekit(Entity):
    id: UUID
    type: str = "resource"
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    status: Optional[Literal["paired", "pairing", "unpaired"]] = "unpaired"


class Light(Entity):
    id: UUID
    id_v1: Optional[str] = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    metadata: Optional[Metadata]
    on: Optional[On]
    dimming: Optional[Dimming]
    dimming_delta: Optional[dict]
    color_temperature: Optional[ColorTemperature]
    color_temperature_delta: Optional[dict]
    color: Optional[Color]
    gradient: Optional[Gradient]
    dynamics: Optional[Dynamics]
    alert: Optional[dict[str, list[str]]]
    signaling: Optional[dict]
    mode: Optional[str]
    effects: Optional[Effects]
    type: Literal["light"] = "light"


class LightLevel(Entity):
    type: Literal["light_level"] = "light_level"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    enabled: Optional[bool]
    light: Optional[LightLevelValue]


class Motion(Entity):
    type: Literal["motion"] = "motion"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    enabled: Optional[bool]
    motion: dict[str, bool]


class Resource(Entity):
    id: UUID
    type: str = "device"
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")


class Room(Entity):
    type: Literal["room"] = "room"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: Optional[list[Identifier]]
    metadata: Optional[Metadata]
    children: Optional[list[Identifier]]


class Scene(Entity):
    id: UUID
    id_v1: Optional[str] = Field(..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    metadata: Optional[Metadata]
    group: Optional[Identifier]
    actions: Optional[list[Actions]]
    palette: Optional[Palette]
    speed: Optional[float]
    auto_dynamic: Optional[bool]
    type: Literal["scene"] = "scene"


class Temperature(Entity):
    type: Literal["temperature"] = "temperature"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    enabled: Optional[bool]
    temperature: Optional[Temp]


class ZGPConnectivity(Entity):
    type: Literal["zgp_connectivity"] = "zgp_connectivity"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    status: Optional[
        Literal[
            "connected", "disconnected", "connectivity_issue", "unidirectional_incoming"
        ]
    ]
    source_id: Optional[str]


class ZigbeeConnectivity(Entity):
    type: Literal["zigbee_connectivity"] = "zigbee_connectivity"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    owner: Optional[Identifier]
    status: Optional[
        Literal[
            "connected", "disconnected", "connectivity_issue", "unidirectional_incoming"
        ]
    ]
    mac_address: Optional[str]


class Zone(Entity):
    type: Literal["zone"] = "zone"
    id: UUID
    id_v1: Optional[str] = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
    services: Optional[list[Identifier]]
    metadata: Optional[Metadata]
    children: Optional[list[Identifier]]
