from types import new_class
from typing import (
    Any,
    Literal,
    Optional,
    Type,
    ClassVar,
    TypeVar,
)
from uuid import UUID as _UUID, uuid4
from typing import TypeVar, Generic
from enum import Enum, auto
from httpx import AsyncClient

from pydantic import BaseConfig, BaseModel, Field
from pydantic.main import ModelMetaclass, BaseModel
from pydantic.generics import GenericModel
from pydantic.dataclasses import dataclass
from requests import delete

try:
    from ujson import dumps, loads
except ImportError:
    try:
        from orjson import dumps, loads
    except ImportError:
        from json import dumps, loads

_type = type
_T = TypeVar("_T")
_D = TypeVar("_D", bound=dict)

__all__ = (
    "Entity",
    "Archetype",
    "RoomType",
    "Attributes",
    "HueEntsV2",
    "HueEntsV1",
    "_XY",
)

# mypy: enable-incomplete-feature=TypeVarTuple
Ent = TypeVar("Ent", bound="Entity")


def default_uuid():
    return UUID(str(uuid4()))


def config_dumps(obj: Any) -> str:
    return ret if isinstance(ret := dumps(obj), str) else ret.decode()


class Config(BaseConfig):
    json_loads = loads
    json_dumps = lambda *args, **kwargs: (
        d if isinstance(d := dumps(*args, **kwargs), str) else d.decode()
    )
    smart_union = True
    allow_mutations = True


class HueConfig(BaseConfig):
    allow_population_by_field_name = True
    json_loads = loads
    json_dumps = lambda *args, **kwargs: (
        d if isinstance(d := dumps(*args, **kwargs), str) else d.decode()
    )
    smart_union = True
    allow_mutation = True


class UUID(_UUID):
    def __json__(self):
        return self.__str__()


def validate(*args, **kwargs):
    return kwargs


class Entity(BaseModel):
    __module__ = "phlyght"
    __cache__: ClassVar[dict[str, Type]] = {}
    id: Optional[UUID] = Field(
        default_factory=lambda: UUID("00000000-0000-0000-0000-000000000000")
    )
    type: ClassVar[str] = "unknown"
    Config = HueConfig
    __config__ = HueConfig

    @classmethod
    def cache_client(cls, client):
        Entity.client = client

    @classmethod
    def get_entities(cls) -> dict[str, Type]:
        return cls.__cache__

    @classmethod
    def get_plural(cls, name):
        if name.endswith("y"):
            return name[:-1] + "ies"
        return name + "s"

    def __new__(cls, client=None, **kwargs):
        clz = type(cls.__name__, (BaseModel,), {}).__new__(cls)
        return clz

    async def get(self):
        return await getattr(self.client, f"get_{self.type}")(self.id)

    async def create(self, **kwargs):
        if not hasattr(self.client, f"create_{self.type}"):
            return

        for k, v in kwargs.items():
            if hasattr(self, k) and getattr(self, k) != v:
                setattr(self, k, v)

        await getattr(self.client, f"create_{self.type}")(self)

    async def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k) and getattr(self, k) != v:
                setattr(self, k, v)
        await getattr(self.client, f"set_{self.type}")(self.id, self)

    async def delete(self):
        if _fn := getattr(self.client, f"delete_{self.type}", None):
            await _fn(self.id, self)

    def __init_subclass__(cls, **_):
        super().__init_subclass__()
        Entity.__cache__[
            _.get_default() if (_ := cls.__fields__.get("type")) else "unknown"
        ] = cls

    def __hash__(self) -> int:
        return hash(self.id)


class BaseAttribute(BaseModel):
    Config = HueConfig
    __config__ = HueConfig

    def __init_subclass__(cls, *args, **kwargs):
        cls.Config = HueConfig


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

    def __json__(self):
        return self.value


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

    def __json__(self):
        return f'"{self.value}"'


_T = TypeVar("_T")


@dataclass
class _XY:
    x: float
    y: float

    def __post_init__(self):
        if self.x < 0.01:
            self.x = 0.01
        if self.y < 0.01:
            self.y = 0.01
        if self.x > 0.99:
            self.x = 0.99
        if self.y > 0.99:
            self.y = 0.99

    def __json__(self):
        return (
            '{"y":' + f'{int(10000*self.x)/10000}, "x": {int(10000*self.y)/10000}' + "}"
        )


@dataclass
class On:
    on: bool = True

    def __json__(self):
        return '{"on": ' + f"{self.on}" + "}"


XY = _XY | tuple[float, float]


class Attributes:
    class Action(BaseAttribute):
        on: "Attributes.On" = Field(default_factory=lambda: Attributes.On(on=True))
        dimming: "Attributes.Dimming" = Field(
            default_factory=lambda: Attributes.Dimming(
                brightness=100.0, min_dim_level=100.0
            )
        )
        color: "Attributes.ColorPoint" = Field(
            default_factory=lambda: Attributes.ColorPoint()
        )
        color_temperature: "Attributes.ScenePaletteColorTemp" = Field(
            default_factory=lambda: Attributes.ScenePaletteColorTemp(mirek=500)
        )
        gradient: "Attributes.Gradient" = Field(
            default_factory=lambda: Attributes.Gradient(points_capable=2, points=[])
        )
        effects: "Attributes.Effects" = Field(
            default_factory=lambda: Attributes.Effects()
        )
        dynamics: "Attributes.SceneDynamics" = Field(
            default_factory=lambda: Attributes.SceneDynamics(duration=1)
        )

    class Actions(BaseAttribute):
        target: "Attributes.Identifier" = Field(...)
        action: "Attributes.Action" = Field(default_factory=lambda: Attributes.Action())
        dimming: "Attributes.Dimming" = Field(
            default_factory=lambda: Attributes.Dimming(
                brightness=100.0, min_dim_level=100.0
            )
        )
        color: "Attributes.ColorPoint" = Field(
            default_factory=lambda: Attributes.ColorPoint()
        )

    class Alert(BaseAttribute):
        action: Literal["breathe", "unknown"] = "unknown"

    class Button(BaseAttribute):
        last_event: Literal[
            "initial_press",
            "repeat",
            "short_release",
            "long_release",
            "double_short_release",
            "long_press",
        ] = "initial_press"

    class Color(BaseAttribute):
        xy: "Attributes.XY" = Field(default_factory=lambda: Attributes.XY(x=0.0, y=0.0))
        gamut: "Attributes.Gamut" = Field(default_factory=lambda: Attributes.Gamut())
        gamut_type: Literal["A", "B", "C"] = "A"

    class ColorPointColor(BaseAttribute):
        color: "Attributes.ColorPoint" = Field(
            default_factory=lambda: Attributes.ColorPoint()
        )

    class ColorPoint(BaseAttribute):
        xy: "Attributes.XY" = Field(default_factory=lambda: Attributes.XY(x=0.0, y=0.0))

    class ColorMirekSchema(BaseAttribute):
        mirek_minimum: int = Field(default=153, ge=153, le=500)
        mirek_maximum: int = Field(default=500, ge=153, le=500)

    class ColorTemp(BaseAttribute):
        mirek: Optional[int] = Field(default=0, ge=153, le=500)
        mirek_valid: Optional[bool] = True
        mirek_schema: Optional["Attributes.ColorMirekSchema"] = Field(
            default_factory=lambda: Attributes.ColorMirekSchema()
        )

    class Dependee(BaseAttribute):
        type: str = "unknown"
        target: "Attributes.Identifier" = Field(...)
        level: str = "unknown"

    class Dimming(BaseAttribute):
        brightness: Optional[float] = Field(default=100, gt=0, le=100)
        min_dim_level: Optional[float] = Field(default=0, ge=0, le=100)

    class DimmingDelta(BaseAttribute):
        action: Optional[Literal["up", "down", "stop"]] = "stop"
        brightness_delta: Optional[float] = Field(default=0, ge=0, le=100)

    class Dynamics(BaseAttribute):
        status: str = "unknown"
        status_values: Optional[list[str]] = Field(default_factory=list)
        speed: Optional[float] = Field(default=0.0, ge=0, le=100)
        speed_valid: Optional[bool] = True

    class Effects(BaseAttribute):
        effect: Optional[list[str]] = Field(default_factory=list)
        status_values: Optional[list[str]] = Field(default_factory=list)
        status: str = "unknown"
        effect_values: Optional[list[str]] = Field(default_factory=list)

    class EntChannel(BaseAttribute):
        channel_id: int = Field(ge=0, le=255)
        position: Optional["Attributes.XYZ"] = Field(
            default_factory=lambda: Attributes.XYZ(x=0.0, y=0.0, z=0.0)
        )
        members: list["Attributes.SegmentRef"] = Field(default_factory=list)

    class EntLocation(BaseAttribute):
        service_location: list["Attributes.ServiceLocation"] = Field(
            default_factory=list
        )

    class Gamut(BaseAttribute):
        red: XY = Field(default_factory=lambda: Attributes.XY(x=0.0, y=0.0))
        green: XY = Field(default_factory=lambda: Attributes.XY(x=0.0, y=0.0))
        blue: XY = Field(default_factory=lambda: Attributes.XY(x=0.0, y=0.0))

    class Gradient(BaseAttribute):
        points: Optional[list["Attributes.ColorPointColor"]] = Field(
            default_factory=list
        )
        points_capable: Optional[int] = Field(default=1, ge=0, le=255)

    class Identifier(BaseAttribute):

        rid: UUID = Field(default_factory=default_uuid)
        rtype: str = "unknown"

    class LightColor(BaseAttribute):
        xy: Optional[XY] = Field(default_factory=lambda: _XY(x=0.0, y=0.0))

    class LightLevelValue(BaseAttribute):
        light_level: Optional[int] = Field(default=0, ge=0, le=100000)
        light_level_valid: Optional[bool] = True

    class LightEffect(BaseAttribute):
        effect: Optional[Literal["fire", "candle", "no_effect"]] = "no_effect"

    class Metadata(BaseAttribute):

        name: str = "unknown"
        archetype: Archetype | RoomType = Archetype.UNKNOWN_ARCHETYPE
        image: "Attributes.Identifier" = Field(
            default_factory=lambda: Attributes.Identifier(), repr=False
        )

    class Motion(BaseAttribute):
        motion: Optional[bool] = False
        motion_valid: Optional[bool] = True

    class On(BaseAttribute):

        on: Optional[bool] = Field(default=True, alias="on")

    class Palette(BaseAttribute):
        color: Optional[list["Attributes.PaletteColor"]] = Field(default_factory=list)
        dimming: Optional[list["Attributes.Dimming"]] = Field(default_factory=list)
        color_temperature: list["Attributes.PaletteTemperature"] = Field(
            default_factory=list
        )

    class PaletteColor(BaseAttribute):
        color: Optional["Attributes.ColorPoint"] = Field(
            default_factory=lambda: Attributes.ColorPoint()
        )
        dimming: Optional["Attributes.Dimming"] = Field(
            default_factory=lambda: Attributes.Dimming(brightness=100.0)
        )

    class PaletteTemperature(BaseAttribute):
        color_temperature: Optional["Attributes.ScenePaletteColorTemp"] = Field(
            default_factory=lambda: Attributes.ScenePaletteColorTemp(mirek=500)
        )
        dimming: Optional["Attributes.Dimming"] = Field(
            default_factory=lambda: Attributes.Dimming(
                brightness=100.0, min_dim_level=100.0
            )
        )

    class PowerState(BaseAttribute):
        battery_state: Optional[Literal["normal", "low", "critical"]] = "normal"
        battery_level: Optional[float] = Field(default=100.0, le=100.0, ge=0.0)

    class ProductData(BaseAttribute):
        model_id: Optional[str] = "unknown"
        manufacturer_name: Optional[str] = "unknown"
        product_name: Optional[str] = "unknown"
        product_archetype: Optional[Archetype] = Archetype.UNKNOWN_ARCHETYPE
        certified: Optional[bool] = False
        software_version: Optional[str] = Field(
            default="0.0.0", regex=r"\d+\.(?:\d+\.)*\d+"
        )
        hardware_platform_type: Optional[str] = "unknown"

    class RelativeRotary(BaseAttribute):
        last_event: Optional["Attributes.RotaryEvent"] = Field(
            default_factory=lambda: Attributes.RotaryEvent()
        )

    class RotaryEvent(BaseAttribute):
        action: Optional[Literal["start", "repeat", "unknown"]] = "unknown"
        rotation: Optional["Attributes.RotaryRotation"] = Field(
            default_factory=lambda: Attributes.RotaryRotation(
                direction="clock_wise", duration=0.0, steps=0
            )
        )

    class RotaryRotation(BaseAttribute):
        direction: Literal["clock_wise", "counter_clock_wise"] = "clock_wise"
        duration: Optional[float] = Field(0.0, ge=0.0)
        steps: Optional[int] = Field(0, ge=0)

    class SceneDynamics(BaseAttribute):
        duration: Optional[int] = Field(0, ge=0)

    class SceneEffects(BaseAttribute):
        effect: Optional[Literal["fire", "candle", "no_effect"]] = "no_effect"

    class ScenePaletteColorTemp(BaseAttribute):
        mirek: int = Field(153, ge=153, le=500)

    class Segment(BaseAttribute):
        start: int = Field(0, ge=0)
        length: int = Field(1, ge=1)

    class SegmentManager(BaseAttribute):
        configurable: Optional[bool] = True
        max_segments: Optional[int] = Field(default=1, ge=1)
        segments: Optional[list["Attributes.Segment"]] = Field(default_factory=list)

    class SegmentRef(BaseAttribute):
        service: "Attributes.Identifier" = Field(
            default_factory=lambda: Attributes.Identifier()
        )
        index: int = 0

    class ServiceLocation(BaseAttribute):
        service: "Attributes.Identifier" = Field(
            default_factory=lambda: Attributes.Identifier()
        )
        position: "Attributes.XYZ" = Field(
            default_factory=lambda: Attributes.XYZ(x=0.0, y=0.0, z=0.0)
        )
        positions: list[Type["Attributes.XYZ"]] = Field(max_items=2, min_items=1)

    class StreamProxy(BaseAttribute):
        mode: Literal["auto", "manual"] = "manual"
        node: "Attributes.Identifier" = Field(
            default_factory=lambda: Attributes.Identifier()
        )

    class Temp(BaseAttribute):
        temperature: float = Field(default=0.0, lt=100.0, gt=-100.0)
        temperature_valid: bool = True

    class TimedEffects(BaseAttribute):
        effect: Optional[str] = "none"
        duration: Optional[float] = Field(default=0.0, ge=0.0)
        status_values: Optional[list[str]] = Field(default_factory=list)
        status: Optional[str] = "unknown"
        effect_values: Optional[list[str]] = Field(default_factory=list)

    class XY(BaseAttribute):
        x: float = Field(0.0, ge=0.0, le=1.0)
        y: float = Field(0.0, ge=0.0, le=1.0)

    class XYZ(BaseAttribute):
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


v: BaseModel

for k, v in Attributes.__dict__.items():
    if k.startswith("__"):
        continue

    if isinstance(v, type) and issubclass(v, BaseModel):
        v.update_forward_refs()


class HueEntsV2:
    class BehaviorInstance(Entity):
        type: ClassVar[str] = "beheavior_instance"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        script_id: str = Field("", regex=r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$")
        enabled: bool = True
        state: dict[str, Any] = Field(default_factory=dict)
        configuration: dict[str, Any] = Field(default_factory=dict)
        dependees: list[Attributes.Dependee] = Field(default_factory=list)
        status: Literal[
            "initializing", "running", "disabled", "errored"
        ] = "initializing"
        last_error: str = "none"
        metadata: dict[Literal["name"], str] = Field(default_factory=dict)
        migrated_from: str = "unknown"

    class BehaviorScript(Entity):
        type: ClassVar[str] = "behavior_script"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        description: str = ""
        configuration_schema: dict[Any, Any] = Field(default_factory=dict)
        trigger_schema: dict[Any, Any] = Field(default_factory=dict)
        state_schema: dict[Any, Any] = Field(default_factory=dict)
        version: str = Field("0.0.1", regex=r"^[0-9]+\.[0-9]+\.[0-9]+$")
        metadata: dict[Any, Any] = Field(default_factory=dict)
        supported_features: list[str] = Field(default_factory=list)
        max_number_of_instances: int = Field(default=0, ge=0, le=255)

    class Bridge(Entity):
        type: ClassVar[str] = "bridge"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        bridge_id: str = ""
        time_zone: dict[str, str] = Field(default_factory=dict)

    class BridgeHome(Entity):
        type: ClassVar[str] = "bridge_home"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        services: list[Attributes.Identifier] = Field(default_factory=list)
        children: list[Attributes.Identifier] = Field(default_factory=list)

    class Button(Entity):
        type: ClassVar[str] = "button"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        metadata: dict[Literal["control_id"], int] = Field(default_factory=dict)
        button: Attributes.Button = Field(default_factory=Attributes.Button)

    class Device(Entity):
        type: ClassVar[str] = "device"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        services: list[Attributes.Identifier] = Field(default_factory=list)
        metadata: Attributes.Metadata = Field(default_factory=Attributes.Metadata)
        product_data: Attributes.ProductData = Field(
            default_factory=lambda: Attributes.ProductData()
        )

    class DevicePower(Entity):
        type: ClassVar[str] = "device_power"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        power_state: Attributes.PowerState = Field(
            default_factory=Attributes.PowerState
        )

    class Entertainment(Entity):
        type: ClassVar[str] = "entertainment"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        renderer: bool = False
        proxy: bool = False
        max_streams: int = Field(1, ge=1)
        segments: Attributes.SegmentManager = Field(
            default_factory=Attributes.SegmentManager
        )

    class EntertainmentConfiguration(Entity):
        type: ClassVar[str] = "entertainment_configuration"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        metadata: dict[Literal["name"], str] = Field(default_factory=dict)
        name: str = ""
        configuration_type: Optional[
            Literal["screen", "monitor", "music", "3dspace", "other"]
        ] = "screen"
        status: Literal["active", "inactive"] = "inactive"
        active_streamer: Attributes.Identifier = Field(
            default_factory=Attributes.Identifier
        )
        stream_proxy: Attributes.StreamProxy = Field(
            default_factory=Attributes.StreamProxy
        )
        channels: list[Attributes.EntChannel] = Field(default_factory=list)
        locations: Attributes.EntLocation = Field(
            default_factory=Attributes.EntLocation
        )
        light_services: list[Attributes.Identifier] = Field(default_factory=list)

    class GeofenceClient(Entity):
        type: ClassVar[str] = "geofence_client"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        name: str = ""

    class Geolocation(Entity):
        type: ClassVar[str] = "geolocation"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        is_configured: bool = False

    class GroupedLight(Entity):
        type: ClassVar[str] = "grouped_light"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        on: Attributes.On = Field(default_factory=Attributes.On)
        alert: Attributes.Alert = Field(default_factory=Attributes.Alert)

    class Homekit(Entity):
        id: UUID
        type: ClassVar[str] = "resource"
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        status: Literal["paired", "pairing", "unpaired"] = "unpaired"

    class Light(Entity):
        # id: UUID
        id_v1: Optional[str] = Field(
            default="", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$", exclude=True
        )
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        metadata: Attributes.Metadata = Field(default_factory=Attributes.Metadata)

        on: Attributes.On = Field(default_factory=Attributes.On)
        dimming: Attributes.Dimming = Field(default_factory=Attributes.Dimming)
        dimming_delta: Attributes.DimmingDelta = Field(
            default_factory=Attributes.DimmingDelta
        )
        color_temperature: Attributes.ColorTemp = Field(
            default_factory=Attributes.ColorTemp
        )
        color_temperature_delta: dict = Field(default_factory=dict)
        color: Attributes.LightColor = Field(default_factory=Attributes.LightColor)
        gradient: Attributes.Gradient = Field(default_factory=Attributes.Gradient)
        dynamics: Attributes.Dynamics = Field(default_factory=Attributes.Dynamics)
        alert: Attributes.Alert = Field(default_factory=Attributes.Alert)
        signaling: dict = Field(default_factory=dict)
        mode: Literal["normal", "streaming"] = "normal"
        effects: Attributes.LightEffect = Field(
            default_factory=lambda: Attributes.LightEffect(effect="fire")
        )
        timed_effects: Attributes.TimedEffects = Field(
            default_factory=Attributes.TimedEffects
        )
        type: ClassVar[str] = "light"

    class LightLevel(Entity):
        type: ClassVar[str] = "light_level"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        enabled: bool = True
        light: Attributes.LightLevelValue = Field(
            default_factory=Attributes.LightLevelValue
        )

    class Motion(Entity):
        type: ClassVar[str] = "motion"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        enabled: bool = True
        motion: Attributes.Motion = Field(default_factory=Attributes.Motion)

    class RelativeRotary(Entity):
        id: UUID
        type: ClassVar[str] = "relative_rotary"
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        relative_rotary: Attributes.RelativeRotary = Field(
            default_factory=Attributes.RelativeRotary
        )

    class Resource(Entity):
        id: UUID
        type: ClassVar[str] = "device"
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")

    class Room(Entity):
        type: ClassVar[str] = "room"
        id: Optional[UUID]
        id_v1: Optional[str] = Field(
            "", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$"
        )
        services: Optional[list[Attributes.Identifier]] = Field(
            default_factory=list, alias="service"
        )
        metadata: Optional[Attributes.Metadata] = Field(
            default_factory=Attributes.Metadata
        )
        children: Optional[list[Attributes.Identifier]] = Field(default_factory=list)

    class Scene(Entity):
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        metadata: Attributes.Metadata = Field(default_factory=Attributes.Metadata)
        group: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        actions: list[Attributes.Actions] = Field(default_factory=list)
        palette: Attributes.Palette = Field(default_factory=Attributes.Palette)
        speed: float = 0.0
        auto_dynamic: bool = False
        type: ClassVar[str] = "scene"

    class Temperature(Entity):
        type: ClassVar[str] = "temperature"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
        enabled: bool = True
        temperature: Attributes.Temp = Field(default_factory=Attributes.Temp)

    class ZGPConnectivity(Entity):
        type: ClassVar[str] = "zgp_connectivity"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
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
        type: ClassVar[str] = "zigbee_connectivity"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        owner: Attributes.Identifier = Field(default_factory=Attributes.Identifier)
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
        type: ClassVar[str] = "zone"
        id: UUID
        id_v1: str = Field("", regex=r"^(\/[a-z]{4,32}\/[0-9a-zA-Z-]{1,32})?$")
        services: list[Attributes.Identifier] = Field(
            default_factory=list, alias="service"
        )
        metadata: Attributes.Metadata = Field(default_factory=Attributes.Metadata)
        children: list[Attributes.Identifier] = Field(default_factory=list)


for k, v in HueEntsV2.__dict__.items():
    if k.startswith("__"):
        continue
    if isinstance(v, type) and issubclass(v, BaseModel):
        v.update_forward_refs()
