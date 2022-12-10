from typing import (
    Any,
    AnyStr,
    Final,
    Generic,
    Literal,
    Optional,
    Type,
    TypeAlias,
    TypeVar,
    ClassVar,
    TypeVarTuple,
)
from uuid import UUID
from enum import Enum, auto

from pydantic import BaseModel, Field

try:
    from ujson import loads, dumps  # type: ignore
except ImportError:
    from orjson import loads, dumps  # type: ignore
except ImportError:  # type: ignore
    from json import loads, dumps  # noqa


__all__ = ("Archetype", "RoomType", "HueEnts")

# mypy: enable-incomplete-feature=TypeVarTuple

_T_M = TypeVarTuple("_T_M")

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


class Attributes:
    class Action(BaseModel):
        on: Optional["Attributes.On"]
        dimming: Optional["Attributes.Dimming"]
        color: Optional["Attributes.ColorPoint"]
        color_temperature: Optional[dict[str, float]]
        gradient: Optional[dict[str, list["Attributes.ColorPoint"]]]
        effects: Optional[dict[str, str]]
        dynamics: Optional[dict[str, float]]

    class Actions(BaseModel):
        target: Optional["Attributes.Identifier"]
        action: Optional["Attributes.Action"]
        dimming: Optional["Attributes.Dimming"]
        color: Optional["Attributes.ColorPoint"]

    class Button(BaseModel):
        last_event: Literal[
            "initial_press",
            "repeat",
            "short_release",
            "long_release",
            "double_short_release",
            "long_press",
        ]

    class Color(BaseModel):
        xy: Optional["Attributes.XY"]
        gamut: Optional["Attributes.Gamut"]
        gamut_type: Optional[Literal["A", "B", "C"]]

    class ColorPoint(BaseModel):
        xy: Optional["Attributes.XY"]

    class ColorTemp(BaseModel):
        mirek: Optional[int]
        mirek_valid: Optional[bool]
        mirek_schema: Optional[dict[str, float]]

    class Dependee(BaseModel):
        type: Optional[str]
        target: Optional["Attributes.Identifier"]
        level: Optional[str]

    class Dimming(BaseModel):
        class Config:
            frozen = True
            allow_mutation = False
            validate_assignment = True

        brightness: Optional[float]
        min_dim_level: Optional[float] = Field(0, repr=False)

    class Dynamics(BaseModel):
        status: Optional[str]
        status_values: Optional[list[str]]
        speed: Optional[float]
        speed_valid: Optional[bool]

    class Effects(BaseModel):
        effect: Optional[list[str]]
        status_values: Optional[list[str]]
        status: Optional[str]
        effect_values: Optional[list[str]]

    class EntChannel(BaseModel):
        channel_id: int = Field(ge=0, le=255)
        position: Optional["Attributes.XYZ"] = None
        members: Optional[list["Attributes.SegmentRef"]]

    class EntLocation(BaseModel):
        service_location: Optional[list["Attributes.ServiceLocation"]]

    class Gamut(BaseModel):
        red: Optional["Attributes.XY"]
        green: Optional["Attributes.XY"]
        blue: Optional["Attributes.XY"]

    class Gradient(BaseModel):
        points: Optional[list["Attributes.ColorPoint"]]
        points_capable: Optional[int]

    class Identifier(BaseModel):
        class Config:
            frozen = True
            allow_mutation = False
            validate_assignment = True

        rid: str
        rtype: str

    class LightLevelValue(BaseModel):
        light_level: Optional[int]
        light_level_valid: Optional[bool]

    class Metadata(BaseModel):
        class Config:
            frozen = True
            allow_mutation = False
            validate_assignment = True

        name: Optional[str]
        archetype: Optional[Archetype | RoomType] = Archetype.UNKNOWN_ARCHETYPE
        image: Optional["Attributes.Identifier"] = Field(None, repr=False)

    class Motion(BaseModel):
        motion: Optional[bool]
        motion_valid: Optional[bool]

    class On(BaseModel):
        class Config:
            frozen = True
            allow_mutation = False
            validate_assignment = True

        on: bool = Field(..., alias="on")

    class Palette(BaseModel):
        color: Optional[list["Attributes.PaletteColor"]]
        dimming: Optional[list["Attributes.Dimming"]]
        color_temperature: Optional[list["Attributes.PaletteTemperature"]]

    class PaletteColor(BaseModel):
        color: Optional["Attributes.ColorPoint"]
        dimming: Optional["Attributes.Dimming"]

    class PaletteTemperature(BaseModel):
        color_temperature: dict[str, float]
        dimming: Optional["Attributes.Dimming"]

    class PowerState(BaseModel):
        battery_state: Literal["normal", "low", "critical"]
        battery_level: float = Field(le=100.0, ge=0.0)

    class ProductData(BaseModel):
        model_id: Optional[str]
        manufacturer_name: Optional[str]
        product_name: Optional[str]
        product_archetype: Optional[Archetype]
        certified: Optional[bool]
        software_version: Optional[str]
        hardware_platform_type: Optional[str]

    class RelativeRotary(BaseModel):
        last_event: Optional["Attributes.RotaryEvent"]

    class RotaryEvent(BaseModel):
        action: Optional[Literal["start", "repeat", "unknown"]]
        rotation: Optional["Attributes.RotaryRotation"]

    class RotaryRotation(BaseModel):
        direction: Optional[Literal["clock_wise", "counter_clock_wise"]]
        duration: Optional[int]
        steps: Optional[int]

    class Segment(BaseModel):
        start: int = Field(..., ge=0)
        length: int = Field(..., ge=1)

    class SegmentManager(BaseModel):
        configurable: Optional[bool]
        max_segments: int = Field(..., ge=1)
        segments: Optional[list["Attributes.Segment"]]

    class SegmentRef(BaseModel):
        service: Optional["Attributes.Identifier"]
        index: Optional[int]

    class ServiceLocation(BaseModel):
        service: Optional["Attributes.Identifier"]
        position: Optional["Attributes.XYZ"] = None
        positions: list[Type["Attributes.XYZ"]] = Field(max_items=2, min_items=1)

    class StreamProxy(BaseModel):
        mode: Literal["auto", "manual"]
        node: Optional["Attributes.Identifier"]

    class Temp(BaseModel):
        temperature: float = Field(lt=100.0, gt=-100.0)
        temperature_valid: Optional[bool]

    class TimedEffects(BaseModel):
        effect: Optional[str]
        duration: Optional[int]
        status_values: Optional[list[str]]
        status: Optional[str]
        effect_values: Optional[list[str]]

    class XY(BaseModel):
        class Config:
            frozen = True
            allow_mutation = False
            validate_assignment = True

        x: Optional[float]
        y: Optional[float]

    class XYZ(BaseModel):
        x: float = Field(ge=-1.0, le=1.0)
        y: float = Field(ge=-1.0, le=1.0)
        z: float = Field(ge=-1.0, le=1.0)


class HueEntsV1:
    class UserConfiguration(Entity):
        name: str
        swupdate: dict
        swupdate2: dict
        whitelist: list[str]
        portalstate: dict
        apiversion: str
        swversion: str
        proxyaddress: str


for k, v in Attributes.__dict__.items():
    if k.startswith("__"):
        continue

    v.update_forward_refs()


class HueEntsV2:
    class BehaviorInstance(Entity):
        type: Final[Literal["behavior_instance"]] = "behavior_instance"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        script_id: Optional[str]
        enabled: Optional[bool]
        state: Optional[dict[str, Any]]
        configuration: Optional[dict[str, Any]]
        dependees: Optional[list[Attributes.Dependee]]
        status: Optional[Literal["initializing", "running", "disabled", "errored"]]
        last_error: Optional[str]
        metadata: Optional[dict[Literal["name"], str]]
        migrated_from: Optional[str] = None

    class BehaviorScript(Entity):
        type: Final[Literal["behavior_script"]] = "behavior_script"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        description: Optional[str]
        configuration_schema: Optional[dict[str, Any]]
        trigger_schema: Optional[dict[str, Any]]
        state_schema: Optional[dict[str, Any]]
        version: Optional[str]
        metadata: Optional[dict[str, str]]

    class Bridge(Entity):
        type: Final[Literal["bridge"]] = "bridge"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        bridge_id: Optional[str]
        time_zone: Optional[dict[str, str]]

    class BridgeHome(Entity):
        type: Final[Literal["bridge_home"]] = "bridge_home"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        services: Optional[list[Attributes.Identifier]]
        children: Optional[list[Attributes.Identifier]]

    class Button(Entity):
        type: Final[Literal["button"]] = "button"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        metadata: Optional[dict[Literal["control_id"], int]]
        button: Optional[Attributes.Button]

    class Device(Entity):
        type: Final[Literal["device"]] = "device"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        services: Optional[list[Attributes.Identifier]]
        metadata: Optional[Attributes.Metadata]
        product_data: Optional[Attributes.ProductData]

    class DevicePower(Entity):
        type: Final[Literal["device_power"]] = "device_power"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        power_state: Optional[Attributes.PowerState]

    class Entertainment(Entity):
        type: Final[Literal["entertainment"]] = "entertainment"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        renderer: Optional[bool]
        proxy: Optional[bool]
        max_streams: Optional[int] = Field(1, ge=1)
        segments: Optional[Attributes.SegmentManager] = None

    class EntertainmentConfiguration(Entity):
        type: Final[
            Literal["entertainment_configuration"]
        ] = "entertainment_configuration"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        metadata: Optional[dict[Literal["name"], str]]
        name: Optional[str] = ""
        configuration_type: Optional[
            Literal["screen", "monitor", "music", "3dspace", "other"]
        ]
        status: Optional[Literal["active", "inactive"]]
        active_streamer: Optional[Attributes.Identifier] = None
        stream_proxy: Optional[Attributes.StreamProxy]
        channels: Optional[list[Attributes.EntChannel]]
        locations: Optional[Attributes.EntLocation] = None
        light_services: Optional[list[Attributes.Identifier]]

    class GeofenceClient(Entity):
        type: Final[Literal["geofence_client"]] = "geofence_client"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        name: Optional[str]

    class Geolocation(Entity):
        type: Final[Literal["geolocation"]] = "geolocation"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        is_configured: Optional[bool] = False

    class GroupedLight(Entity):
        type: Final[Literal["grouped_light"]] = "grouped_light"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        on: Optional[Attributes.On] = Field(repr=False)
        alert: Optional[dict[str, list[str]]]

    class Homekit(Entity):
        id: UUID
        type: Final[Literal["resource"]] = "resource"
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        status: Optional[Literal["paired", "pairing", "unpaired"]] = "unpaired"

    class Light(Entity):
        id: UUID
        id_v1: Optional[str] = Field(
            ..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        metadata: Optional[Attributes.Metadata]
        on: Optional[Attributes.On]
        dimming: Optional[Attributes.Dimming]
        dimming_delta: Optional[dict]
        color_temperature: Optional[Attributes.ColorTemp]
        color_temperature_delta: Optional[dict]
        color: Optional[Attributes.Color]
        gradient: Optional[Attributes.Gradient]
        dynamics: Optional[Attributes.Dynamics]
        alert: Optional[dict[str, list[str]]]
        signaling: Optional[dict]
        mode: Optional[str]
        effects: Optional[Attributes.Effects]
        type: Final[Literal["light"]] = "light"

    class LightLevel(Entity):
        type: Final[Literal["light_level"]] = "light_level"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        enabled: Optional[bool]
        light: Optional[Attributes.LightLevelValue]

    class Motion(Entity):
        type: Final[Literal["motion"]] = "motion"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        enabled: Optional[bool]
        motion: Optional[Attributes.Motion]

    class RelativeRotary(Entity):
        id: UUID
        type: Final[Literal["relative_rotary"]] = "relative_rotary"
        owner: Optional[Attributes.Identifier]
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        relative_rotary: Optional[Attributes.RelativeRotary]

    class Resource(Entity):
        id: UUID
        type: Final[Literal["device"]] = "device"
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")

    class Room(Entity):
        type: Final[Literal["room"]] = "room"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        services: Optional[list[Attributes.Identifier]]
        metadata: Optional[Attributes.Metadata]
        children: Optional[list[Attributes.Identifier]]

    class Scene(Entity):
        id: UUID
        id_v1: Optional[str] = Field(
            ..., regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        metadata: Optional[Attributes.Metadata]
        group: Optional[Attributes.Identifier]
        actions: Optional[list[Attributes.Actions]]
        palette: Optional[Attributes.Palette]
        speed: Optional[float]
        auto_dynamic: Optional[bool]
        type: Final[Literal["scene"]] = "scene"

    class Temperature(Entity):
        type: Final[Literal["temperature"]] = "temperature"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        enabled: Optional[bool]
        temperature: Optional[Attributes.Temp]

    class ZGPConnectivity(Entity):
        type: Final[Literal["zgp_connectivity"]] = "zgp_connectivity"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        status: Optional[
            Literal[
                "connected",
                "disconnected",
                "connectivity_issue",
                "unidirectional_incoming",
            ]
        ]
        source_id: Optional[str]

    class ZigbeeConnectivity(Entity):
        type: Final[Literal["zigbee_connectivity"]] = "zigbee_connectivity"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        owner: Optional[Attributes.Identifier]
        status: Optional[
            Literal[
                "connected",
                "disconnected",
                "connectivity_issue",
                "unidirectional_incoming",
            ]
        ]
        mac_address: Optional[str]

    class Zone(Entity):
        type: Final[Literal["zone"]] = "zone"
        id: UUID
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        services: Optional[list[Attributes.Identifier]]
        metadata: Attributes.Metadata
        children: Optional[list[Attributes.Identifier]]


for k, v in HueEntsV2.__dict__.items():
    if k.startswith("__"):
        continue

    v.update_forward_refs()
