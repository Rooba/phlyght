from typing import (
    Any,
    Final,
    Literal,
    Optional,
    Type,
    ClassVar,
)
from uuid import UUID
from enum import Enum, auto


from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

try:
    from ujson import loads, dumps
except ImportError:
    try:
        from orjson import loads, dumps
    except ImportError:
        from json import loads, dumps

_type = type

__all__ = (
    "Entity",
    "Archetype",
    "RoomType",
    "HueEntsV2",
    "HueEntsV1",
    "Action",
    "Actions",
    "Alert",
    "Button",
    "Color",
    "ColorMirekSchema",
    "ColorPoint",
    "ColorPointColor",
    "ColorTemp",
    "EntChannel",
    "LightColor",
    "PaletteColor",
    "ScenePaletteColorTemp",
    "Dependee",
    "Dimming",
    "DimmingDelta",
    "Dynamics",
    "SceneDynamics",
    "ProductData",
    "Effects",
    "EntLocation",
    "LightEffect",
    "SceneEffects",
    "TimedEffects",
    "RotaryEvent",
    "Gamut",
    "Gradient",
    "Identifier",
    "LightLevelValue",
    "ServiceLocation",
    "Motion",
    "SegmentManager",
)

# mypy: enable-incomplete-feature=TypeVarTuple


class Entity(BaseModel):
    __module__ = "phlyght"
    __cache__: ClassVar[dict[str, Type]] = {}
    id: UUID = Field(
        default_factory=lambda: UUID("00000000-0000-0000-0000-000000000000")
    )
    type: ClassVar[str] = "unknown"

    class Config:
        __root__: "Entity"
        json_loads = loads
        json_dumps = dumps
        smart_union = True

    @classmethod
    def get_entities(cls) -> dict[str, Type]:
        return cls.__cache__

    @classmethod
    def __prepare__(cls, name, bases, **kwds):
        return super().__prepare__(name, bases, **kwds)

    def __init_subclass__(cls, **_):
        super().__init_subclass__()
        Entity.__cache__[
            _.get_default() if (_ := cls.__fields__.get("type")) else "unknown"
        ] = cls

    def __hash__(self) -> int:
        return hash(self.id)


class RoomType(Enum):
    @staticmethod
    def _generate_next_value_(name, *_):
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
    def _generate_next_value_(name, *_):
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


class Config:
    json_dumps = dumps
    json_loads = loads
    smart_union = True


@dataclass(config=Config)
class _XY:
    x: float = Field(0.0, ge=0.0, le=1.0)
    y: float = Field(0.0, ge=0.0, le=1.0)


@dataclass(config=Config)
class On:
    on: bool = True


@dataclass(config=Config)
class LightEffect:
    effect: Literal["fire", "candle", "no_effect"] = "no_effect"


XY = _XY | tuple[float, float]


@dataclass(config=Config)
class Action:
    on: On = Field(default_factory=On)
    dimming: "Dimming" = Field(default_factory=lambda: Dimming())
    color: "ColorPoint" = Field(default_factory=lambda: ColorPoint())
    color_temperature: "ScenePaletteColorTemp" = Field(
        default_factory=lambda: ScenePaletteColorTemp()
    )
    gradient: "Gradient" = Field(default_factory=lambda: Gradient())
    effects: "Effects" = Field(default_factory=lambda: Effects())
    dynamics: "SceneDynamics" = Field(default_factory=lambda: SceneDynamics())


@dataclass(config=Config)
class Actions:
    target: "Identifier" = Field(default_factory=lambda: Identifier())
    action: "Action" = Field(default_factory=lambda: Action())
    dimming: "Dimming" = Field(default_factory=lambda: Dimming())
    color: "ColorPoint" = Field(default_factory=lambda: ColorPoint())


@dataclass(config=Config)
class Alert:
    action: Literal["breathe", "unknown"] = "unknown"


@dataclass(config=Config)
class Button:
    last_event: Literal[
        "initial_press",
        "repeat",
        "short_release",
        "long_release",
        "double_short_release",
        "long_press",
    ] = "initial_press"


@dataclass(config=Config)
class Color:
    xy: XY = Field(default_factory=_XY)
    gamut: "Gamut" = Field(default_factory=lambda: Gamut())
    gamut_type: Literal["A", "B", "C"] = "A"


@dataclass(config=Config)
class ColorPointColor:
    color: "ColorPoint" = Field(default_factory=lambda: ColorPoint())


@dataclass(config=Config)
class ColorPoint:
    xy: XY = Field(default_factory=_XY)


@dataclass(config=Config)
class ColorMirekSchema:
    mirek_minimum: int = Field(153, ge=153, le=500)
    mirek_maximum: int = Field(500, ge=153, le=500)


@dataclass(config=Config)
class ColorTemp:
    mirek: Optional[int] = Field(0, ge=153, le=500)
    mirek_valid: bool = True
    mirek_schema: ColorMirekSchema = Field(default_factory=ColorMirekSchema)


@dataclass(config=Config)
class Dependee:
    type: str = "unknown"
    target: "Identifier" = Field(default_factory=lambda: Identifier())
    level: str = "unknown"


@dataclass(config=Config)
class Dimming:
    brightness: float = Field(1, gt=0, le=100)
    min_dim_level: float = Field(0, ge=0, le=100)


@dataclass(config=Config)
class DimmingDelta:
    action: Literal["up", "down", "stop"] = "stop"
    brightness_delta: float = Field(0, ge=0, le=100)


@dataclass(config=Config)
class Dynamics:
    status: str = "unknown"
    status_values: list[str] = Field(default_factory=list)
    speed: float = Field(0.0, ge=0, le=100)
    speed_valid: bool = True


@dataclass(config=Config)
class Effects:
    effect: list[str] = Field(default_factory=list)
    status_values: list[str] = Field(default_factory=list)
    status: str = "unknown"
    effect_values: list[str] = Field(default_factory=list)


@dataclass(config=Config)
class EntChannel:
    channel_id: int = Field(0, ge=0, le=255)
    position: "XYZ" = Field(default_factory=lambda: XYZ())
    members: list["SegmentRef"] = Field(default_factory=list)


@dataclass(config=Config)
class EntLocation:
    service_location: list["ServiceLocation"] = Field(default_factory=list)


@dataclass(config=Config)
class Gamut:
    red: XY = Field(default_factory=_XY)
    green: XY = Field(default_factory=_XY)
    blue: XY = Field(default_factory=_XY)


@dataclass(config=Config)
class Gradient:
    points: list[ColorPointColor] = Field(default_factory=list)
    points_capable: int = Field(1, ge=0, le=255)


@dataclass(config=Config)
class Identifier:

    rid: UUID = Field(
        default_factory=lambda: UUID("00000000-0000-0000-0000-000000000000")
    )
    rtype: str = "unknown"


@dataclass(config=Config)
class LightColor:
    xy: XY = 0.0, 0.0


@dataclass(config=Config)
class LightLevelValue:
    light_level: int = Field(0, ge=0, le=100000)
    light_level_valid: bool = True


@dataclass(config=Config)
class Metadata:

    name: str = "unknown"
    archetype: Archetype | RoomType = Archetype.UNKNOWN_ARCHETYPE
    image: Identifier = Field(default_factory=Identifier)


@dataclass(config=Config)
class Motion:
    motion: bool = False
    motion_valid: bool = True


@dataclass(config=Config)
class Palette:
    color: list["PaletteColor"] = Field(default_factory=list)
    dimming: list["Dimming"] = Field(default_factory=list)
    color_temperature: list["PaletteTemperature"] = Field(default_factory=list)


@dataclass(config=Config)
class PaletteColor:
    color: ColorPoint = Field(default_factory=ColorPoint)
    dimming: Dimming = Field(default_factory=Dimming)


@dataclass(config=Config)
class PaletteTemperature:
    color_temperature: "ScenePaletteColorTemp" = Field(
        default_factory=lambda: ScenePaletteColorTemp()
    )
    dimming: Dimming = Field(default_factory=Dimming)


@dataclass(config=Config)
class PowerState:
    battery_state: Literal["normal", "low", "critical"] = "normal"
    battery_level: float = Field(100.0, le=100.0, ge=0.0)


@dataclass(config=Config)
class ProductData:
    model_id: str = "unknown"
    manufacturer_name: str = "unknown"
    product_name: str = "unknown"
    product_archetype: Archetype = Archetype.UNKNOWN_ARCHETYPE
    certified: bool = False
    software_version: str = Field("0.0.0", regex=r"\d+\.\d+\.\d+")
    hardware_platform_type: str = "unknown"


@dataclass(config=Config)
class RelativeRotary:
    last_event: "RotaryEvent" = Field(default_factory=lambda: RotaryEvent())


@dataclass(config=Config)
class RotaryEvent:
    action: Literal["start", "repeat", "unknown"] = "unknown"
    rotation: "RotaryRotation" = Field(default_factory=lambda: RotaryRotation())


@dataclass(config=Config)
class RotaryRotation:
    direction: Literal["clock_wise", "counter_clock_wise"] = "clock_wise"
    duration: float = Field(0.0, ge=0.0)
    steps: int = Field(0, ge=0)


@dataclass(config=Config)
class SceneDynamics:
    duration: int = Field(0, ge=0)


@dataclass(config=Config)
class SceneEffects:
    effect: Literal["fire", "candle", "no_effect"] = "no_effect"


@dataclass(config=Config)
class ScenePaletteColorTemp:
    mirek: int = Field(153, ge=153, le=500)


@dataclass(config=Config)
class Segment:
    start: int = Field(0, ge=0)
    length: int = Field(1, ge=1)


@dataclass(config=Config)
class SegmentManager:
    configurable: bool = True
    max_segments: int = Field(1, ge=1)
    segments: list["Segment"] = Field(default_factory=list)


@dataclass(config=Config)
class SegmentRef:
    service: Identifier = Field(default_factory=Identifier)
    index: int = 0


@dataclass(config=Config)
class ServiceLocation:
    service: Identifier = Field(default_factory=Identifier)
    position: "XYZ" = Field(default_factory=lambda: XYZ())
    positions: list[Type["XYZ"]] = Field(max_items=2, min_items=1)


@dataclass(config=Config)
class StreamProxy:
    mode: Literal["auto", "manual"] = "manual"
    node: Identifier = Field(default_factory=Identifier)


@dataclass(config=Config)
class Temp:
    temperature: float = Field(0.0, lt=100.0, gt=-100.0)
    temperature_valid: bool = True


@dataclass(config=Config)
class TimedEffects:
    effect: str = "none"
    duration: float = Field(0.0, ge=0.0)
    status_values: list[str] = Field(default_factory=list)
    status: str = "unknown"
    effect_values: list[str] = Field(default_factory=list)


@dataclass(config=Config)
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


class HueEntsV2:
    class BehaviorInstance(Entity):
        type: Final[Literal["behavior_instance"]] = "behavior_instance"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        script_id: str = Field("", regex=r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$")
        enabled: bool = True
        state: dict[str, Any] = Field(default_factory=dict)
        configuration: dict[str, Any] = Field(default_factory=dict)
        dependees: list[Dependee] = Field(default_factory=list)
        status: Literal[
            "initializing", "running", "disabled", "errored"
        ] = "initializing"
        last_error: str = "none"
        metadata: dict[Literal["name"], str] = Field(default_factory=dict)
        migrated_from: str = "unknown"

    class BehaviorScript(Entity):
        type: Final[Literal["behavior_script"]] = "behavior_script"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        description: str = ""
        configuration_schema: dict[str, Any] = Field(default_factory=dict)
        trigger_schema: dict[str, Any] = Field(default_factory=dict)
        state_schema: dict[str, Any] = Field(default_factory=dict)
        version: str = Field("0.0.1", regex=r"^[0-9]+\.[0-9]+\.[0-9]+$")
        metadata: dict[str, str] = Field(default_factory=dict)

    class Bridge(Entity):
        type: Final[Literal["bridge"]] = "bridge"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        bridge_id: str = ""
        time_zone: dict[str, str] = Field(default_factory=dict)

    class BridgeHome(Entity):
        type: Final[Literal["bridge_home"]] = "bridge_home"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        services: list[Identifier] = Field(default_factory=list)
        children: list[Identifier] = Field(default_factory=list)

    class Button(Entity):
        type: Final[Literal["button"]] = "button"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier = Identifier()
        metadata: dict[Literal["control_id"], int] = Field(default_factory=dict)
        button: Button = Button()

    class Device(Entity):
        type: Final[Literal["device"]] = "device"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        services: list[Identifier] = Field(default_factory=list)
        metadata: Metadata = Metadata()
        product_data: ProductData = ProductData()

    class DevicePower(Entity):
        type: Final[Literal["device_power"]] = "device_power"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier = Identifier()
        power_state: PowerState = PowerState()

    class Entertainment(Entity):
        type: Final[Literal["entertainment"]] = "entertainment"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier = Identifier()
        renderer: bool = False
        proxy: bool = False
        max_streams: int = Field(1, ge=1)
        segments: SegmentManager = SegmentManager()

    class EntertainmentConfiguration(Entity):
        type: Final[
            Literal["entertainment_configuration"]
        ] = "entertainment_configuration"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        metadata: dict[Literal["name"], str] = Field(default_factory=dict)
        name: str = ""
        configuration_type: Optional[
            Literal["screen", "monitor", "music", "3dspace", "other"]
        ] = "screen"
        status: Literal["active", "inactive"] = "inactive"
        active_streamer: Identifier = Identifier()
        stream_proxy: StreamProxy = StreamProxy()
        channels: list[EntChannel] = Field(default_factory=list)
        locations: EntLocation = EntLocation()
        light_services: list[Identifier] = Field(default_factory=list)

    class GeofenceClient(Entity):
        type: Final[Literal["geofence_client"]] = "geofence_client"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        name: str = ""

    class Geolocation(Entity):
        type: Final[Literal["geolocation"]] = "geolocation"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        is_configured: bool = False

    class GroupedLight(Entity):
        type: Final[Literal["grouped_light"]] = "grouped_light"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        on: On = On()
        alert: Alert = Alert()

    class Homekit(Entity):
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        type: Final[Literal["resource"]] = "resource"
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        status: Literal["paired", "pairing", "unpaired"] = "unpaired"

    class Light(Entity):
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$", exclude=True
        )
        owner: Identifier = Identifier()
        metadata: Metadata = Metadata()

        on: On = On()
        dimming: Dimming = Dimming()
        dimming_delta: DimmingDelta = DimmingDelta()
        color_temperature: ColorTemp = ColorTemp()
        color_temperature_delta: dict = Field(default_factory=dict)
        color: LightColor | dict[Literal["xy"], tuple[float, float]] = LightColor()
        gradient: Gradient = Gradient()
        dynamics: Dynamics = Dynamics()
        alert: Alert = Alert()
        signaling: dict = Field(default_factory=dict)
        mode: Literal["normal", "streaming"] = "normal"
        effects: LightEffect = LightEffect(effect="fire")
        timed_effects: TimedEffects = TimedEffects()
        type: Final[Literal["light"]] = "light"

    class LightLevel(Entity):
        type: Final[Literal["light_level"]] = "light_level"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier = Identifier()
        enabled: bool = True
        light: LightLevelValue = LightLevelValue()

    class Motion(Entity):
        type: Final[Literal["motion"]] = "motion"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier = Identifier()
        enabled: bool = True
        motion: Motion = Motion()

    class RelativeRotary(Entity):
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        type: Final[Literal["relative_rotary"]] = "relative_rotary"
        owner: Identifier = Identifier()
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        relative_rotary: RelativeRotary = RelativeRotary()

    class Resource(Entity):
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        type: Final[Literal["device"]] = "device"
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")

    class Room(Entity):
        type: Final[Literal["room"]] = "room"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        services: list[Identifier] = Field(default_factory=list)
        metadata: Metadata = Metadata()
        children: list[Identifier] = Field(default_factory=list)

    class Scene(Entity):
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        metadata: Metadata = Metadata()
        group: Identifier = Identifier()
        actions: list[Actions] = Field(default_factory=list)
        palette: Palette = Palette()
        speed: float = 0.0
        auto_dynamic: bool = False
        type: Final[Literal["scene"]] = "scene"

    class Temperature(Entity):
        type: Final[Literal["temperature"]] = "temperature"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier = Identifier()
        enabled: bool = True
        temperature: Temp = Temp()

    class ZGPConnectivity(Entity):
        type: Final[Literal["zgp_connectivity"]] = "zgp_connectivity"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier = Identifier()
        status: Optional[
            Literal[
                "connected",
                "disconnected",
                "connectivity_issue",
                "unidirectional_incoming",
            ]
        ] = "connected"
        source_id: str = ""

    class ZigbeeConnectivity(Entity):
        type: Final[Literal["zigbee_connectivity"]] = "zigbee_connectivity"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Identifier = Identifier()
        status: Optional[
            Literal[
                "connected",
                "disconnected",
                "connectivity_issue",
                "unidirectional_incoming",
            ]
        ] = "connected"
        mac_address: str = Field("", regex=r"^(?:[0-9a-fA-F]{2}(?:-|:)?){6}$")

    class Zone(Entity):
        type: Final[Literal["zone"]] = "zone"
        id: UUID = UUID("00000000-0000-0000-0000-000000000000")
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        services: list[Identifier] = Field(default_factory=list)
        metadata: Metadata = Metadata()
        children: list[Identifier] = Field(default_factory=list)


for k, v in HueEntsV2.__dict__.items():
    if k.startswith("__"):
        continue

    if isinstance(v, type) and issubclass(v, BaseModel):
        v.update_forward_refs()
