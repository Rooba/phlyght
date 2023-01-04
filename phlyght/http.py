from abc import abstractmethod
from asyncio import gather, get_running_loop, new_event_loop, sleep
from inspect import signature, Parameter
from re import compile
from typing import Any, Literal, Optional, TypeVar, Generic
from time import time

from httpx import AsyncClient, ConnectError, ConnectTimeout, _content
from httpx._urls import URL as _URL
from httpx._exceptions import ReadTimeout as HTTPxReadTimeout
from httpcore._exceptions import ReadTimeout
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass
from pydantic.generics import GenericModel
from yaml import Loader, load

from . import models
from .models import HueEntsV2, Entity, UUID


try:
    from ujson import dumps, loads, JSONDecodeError
except ImportError:
    try:
        from orjson import dumps, loads, JSONDecodeError
    except ImportError:
        from json import dumps, loads, JSONDecodeError

setattr(_content, "json_dumps", dumps)

try:
    from yarl import URL as UR
except ImportError:
    ...

try:
    from rich import print  # noqa
except ImportError:
    ...

_T = TypeVar("_T")

__all__ = ("Router", "route", "RouterMeta", "SubRouter", "HueAPIv2")

ENDPOINT_METHOD = compile(r"^(?=((?:get|set|create|delete)\w+))\1")
STR_FMT_RE = compile(r"(?=(\{([^:]+)(?::([^}]+))?\}))\1")
URL_TYPES = {"str": str, "int": int}
IP_RE = compile(r"(?=(?:(?<=[^0-9])|)((?:[0-9]{,3}\.){3}[0-9]{,3}))\1")

MSG_RE_BYTES = compile(
    rb"(?=((?P<hello>^: hi\n\n$)|^id:\s(?P<id>[0-9]+:\d*?)\ndata:(?P<data>[^$]+)\n\n))\1"
)
MSG_RE_TEXT = compile(
    r"(?=((?P<hello>^: hi\n\n$)|^id:\s(?P<id>[0-9]+:\d*?)\ndata:(?P<data>[^$]+)\n\n))\1"
)
TYPE_CACHE = {}

for k, v in HueEntsV2.__dict__.items():
    if k.startswith("__") or not issubclass(v, BaseModel):
        continue
    TYPE_CACHE[getattr(v, "type")] = v


@dataclass()
class PhlyghtConfig:
    ...


def get_url_args(url):
    kwds = {}
    match = STR_FMT_RE.finditer(url)
    for m in match:
        name = m.group(2)
        if len(m.groups()) >= 4:
            type_ = URL_TYPES[m.group(3)]
        else:
            type_ = str
        kwds[name] = type_
    return kwds


class Event(GenericModel, Generic[_T]):
    class Config:
        __root__ = _T

    id: str
    object: _T
    type: str


class LRUItem(BaseModel):
    access_time: int = Field(default_factory=lambda: int(time()))
    value: Any = object()

    def __id__(self):
        return id(self.value)

    def __hash__(self):
        return hash(self.value)


class LRU(set):
    def __init__(self, maxsize, /, *items):
        super().__init__()
        self.maxsize = maxsize
        for item in items[:maxsize]:
            self.add(LRUItem(value=item))

    def add(self, item):
        if len(self) + 1 > self.maxsize:
            new = self ^ set(
                sorted(self, key=lambda x: x.access_time)[::-1][
                    : len(self) + 1 - self.maxsize
                ]
            )
            old = self - new
            for fut in old:
                fut.value.cancel()
            self -= old

        super().add(LRUItem(value=item))

    def pop(self):
        super().pop().value

    def remove(self, item):
        super().remove(*filter(lambda x: x.value == item, self))

    def extend(self, *items):
        len_new = len(self) + len(items)
        if len_new > self.maxsize:
            new = self ^ set(
                sorted(self, key=lambda x: x.access_time)[::-1][
                    : len_new - self.maxsize
                ]
            )
            old = self - new
            for fut in old:
                fut.value.cancel()
            self -= old
        self |= set([LRUItem(value=item) for item in items])


class URL(_URL):
    def __truediv__(self, other):
        # Why am i doing this? good question.
        try:
            return URL(str(UR(f"{self}") / other.lstrip("/")))
        except NameError:
            return URL(f"{self}{other.lstrip('/')}")

    def __floordiv__(self, other):
        try:
            return URL(str(UR(f"{self}") / other.lstrip("/")))
        except NameError:
            return URL(f"{self}{other.lstrip('/')}")


def ret_cls(cls):
    def wrapped(fn):
        async def sub_wrap(self, *args, **kwargs):
            try:
                ret = loads(
                    (await fn(self, *args, **kwargs))
                    .content.decode()
                    .rstrip("\\r\\n")
                    .lstrip(" ")
                )

                kwargs.pop("base_uri", None)
                ret = ret.get("data", [])
                _rets = []

                if isinstance(ret, list):
                    for r in ret:
                        _rets.append(cls(**r))
                else:
                    return cls(**ret)
                return _rets
            except JSONDecodeError:
                return []

        return sub_wrap

    return wrapped


def route(method, endpoint) -> Any:
    def wrapped(fn):
        async def sub_wrap(
            self: "SubRouter",
            *args,
            base_uri=None,
            content: Optional[bytes] = None,
            data: Optional[dict[str, str]] = None,
            params: Optional[dict[str, str]] = None,
            **kwargs,
        ):
            params = params or {}
            data = data or {}
            json = {}
            args = set(args)
            if "headers" in kwargs:
                headers = self._headers | kwargs.pop("headers")
            else:
                headers = self._headers

            ents = set(filter(lambda x: isinstance(x, Entity), args))
            args = tuple(args - ents)
            ent: BaseModel

            for ent in ents:
                json |= loads(
                    ent.json(exclude_unset=True, exclude_none=True, skip_defaults=True)
                )

            for param_name, param in signature(fn).parameters.items():
                if param_name == "self":
                    continue

                if param.kind == Parameter.POSITIONAL_ONLY:
                    data[param_name] = param.annotation(str(args[0]))
                    if len(args) > 1:
                        args = args[1:]

                else:
                    if param_name in fn.__annotations__:
                        anno = fn.__annotations__[param_name]
                        if isinstance(anno, type):
                            type_ = anno
                        elif anno._name == "Optional":
                            if hasattr(anno.__args__[0], "_name"):
                                type_ = str
                            else:
                                type_ = anno.__args__[0]
                        else:
                            type_ = fn.__annotations__[param_name]
                    else:
                        type_ = str

                    if param.default is param.empty:
                        if param_name not in kwargs and param_name not in data:
                            raise TypeError(
                                f"Missing required argument {param_name} for {fn.__name__}"
                            )
                        if param_name in kwargs:
                            data[param_name] = type_(kwargs.pop(param_name))

                    else:
                        if v := kwargs.pop(param_name, param.default):
                            data[param_name] = type_(v)

            url_args = get_url_args(endpoint)
            for k, v in url_args.items():
                if k not in kwargs and k not in params and k not in data:
                    raise ValueError(f"Missing required argument {k}")
                if k in kwargs:
                    url_args[k] = v(kwargs.pop(k))
                elif k in params:
                    url_args[k] = v(params.pop(k))  # type: ignore
                elif k in data:
                    url_args[k] = v(data.pop(k))

            try:
                if kwargs:
                    data = data | kwargs if data else kwargs
            except Exception:
                ...
            _match_bridge = IP_RE.search(self._bridge_ip)
            if not _match_bridge:
                raise ValueError(f"Invalid bridge ip {self._bridge_ip}")

            _url_base = f"https://{_match_bridge.group(1)}/" + f"{base_uri}".lstrip("/")
            if url_args:
                new_endpoint = URL(_url_base) / endpoint.format(**url_args)
            else:
                new_endpoint = URL(_url_base) / endpoint

            if headers and headers.get("Accept", "") == "text/event-stream":
                return self._client.stream(
                    method,
                    new_endpoint,
                    content=content,
                    data=data,
                    params=params,
                    headers=headers,
                )
            else:
                resp = await self._client.request(
                    method,
                    new_endpoint,
                    content=content,
                    data=data,
                    params=params,
                    headers=headers,
                    json=json,
                )
                return resp

        return sub_wrap

    return wrapped


class RouterMeta(type):
    @classmethod
    def __prepare__(cls, _, bases, **kwargs):
        if bases:
            return kwargs | bases[0].__dict__
        return kwargs

    def __new__(cls, _, bases, kwds, **kwargs):
        cells = {}
        _base = kwds.get("BASE_URI", "")

        def set_key(v):
            def wrap(self, *args, **_kwds):
                return v(self, *args, base_uri=_base, **_kwds)

            return wrap

        if any(
            map(
                lambda x: ENDPOINT_METHOD.match(x) is not None,
                kwds.keys(),
            )
        ):
            funcs = list(
                filter(
                    lambda k: (
                        ENDPOINT_METHOD.match(k[0]) is not None and callable(k[1])
                    ),
                    kwds.items(),
                )
            )
            for k, v in funcs:
                if hasattr(v, "__closure__"):
                    # val = v.__closure__[0].cell_contents
                    cells[k] = set_key(v)

        kwds["handlers"] = cells

        for base in bases:
            if hasattr(base, "handlers"):
                kwds["handlers"] |= base.handlers

        kwds.update(**kwds["handlers"])

        return super().__new__(cls, cls.__name__, bases, kwds, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SubRouter(metaclass=RouterMeta):
    BASE_URI: str
    _api_path: str
    _client: AsyncClient
    _bridge_ip: str

    def __new__(cls, hue_api_key: str):
        if not hasattr(cls, "handlers"):
            cls.handlers: dict[str, type] = {}

        for base in cls.__bases__:
            if hasattr(base, "handlers"):
                cls.handlers |= getattr(base, "handlers")

        return super().__new__(cls)

    def __init__(self, hue_api_key: str):
        self._hue_api_key = hue_api_key
        self._headers = {
            "User-Agent": "Python/HueClient",
            "hue-application-key": self._hue_api_key,
        }

    def __init_subclass__(cls, *_, **kwargs) -> None:
        super().__init_subclass__()
        if kwargs.get("root"):
            cls._api_path = f'{kwargs.get("root")}{cls.BASE_URI}'

    def __getattribute__(self, key) -> Any:
        return object.__getattribute__(self, key)


class HueAPIv1(SubRouter):
    BASE_URL = ""


class HueAPIv2(SubRouter):
    BASE_URI = "/clip/v2"

    @ret_cls(HueEntsV2.Light)
    @route("GET", "/resource/light")
    async def get_lights(self, friendly_name: Optional[str] = None):
        ...

    @ret_cls(HueEntsV2.Light)
    @route("GET", "/resource/light/{light_id}")
    async def get_light(self, light_id: str, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/light/{light_id}")
    async def set_light(
        self,
        light_id: UUID,
        /,
        on: Optional[dict[Literal["on"], bool]] = None,
        dimming: Optional[dict[str, Any]] = None,
        dimming_delta: Optional[dict] = None,
        color_temperature: Optional[int] = None,
        color_temperature_delta: Optional[dict] = None,
        color: Optional[dict] = None,
        dynamics: Optional[dict] = None,
        alert: Optional[dict] = None,
        gradient: Optional[dict] = None,
        effects: Optional[dict] = None,
        timed_effects: Optional[dict] = None,
    ):
        ...

    @ret_cls(HueEntsV2.Scene)
    @route("GET", "/resource/scene")
    async def get_scenes(self):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("POST", "/resource/scene")
    async def create_scene(self, **kwargs):
        ...

    @ret_cls(HueEntsV2.Scene)
    @route("GET", "/resource/scene/{scene_id}")
    async def get_scene(self, scene_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/scene/{scene_id}")
    async def set_scene(self, scene_id: UUID, /, **kwargs):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("DELETE", "/resource/scene/{scene_id}")
    async def delete_scene(self, scene_id: UUID, /):
        ...

    @ret_cls(HueEntsV2.Room)
    @route("GET", "/resource/room")
    async def get_rooms(self):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("POST", "/resource/room")
    async def create_room(self, **kwargs):
        ...

    @ret_cls(HueEntsV2.Room)
    @route("GET", "/resource/room/{room_id}")
    async def get_room(self, room_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/room/{room_id}")
    async def set_room(
        self,
        room_id: UUID,
        /,
        metadata: Optional[dict[str, str]] = None,
        children: Optional[models.Attributes.Identifier] = None,
    ):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("DELETE", "/resource/room/{room_id}")
    async def delete_room(self, room_id: UUID):
        ...

    @ret_cls(HueEntsV2.Zone)
    @route("GET", "/resource/zone")
    async def get_zones(self):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("POST", "/resource/zone")
    async def create_zone(self, **kwargs):
        ...

    @ret_cls(HueEntsV2.Zone)
    @route("GET", "/resource/zone/{zone_id}")
    async def get_zone(self, zone_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/zone/{zone_id}")
    async def set_zone(self, zone_id: UUID, /, **kwargs):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("DELETE", "/resource/zone/{zone_id}")
    async def delete_zone(self, zone_id: UUID, /):
        ...

    @ret_cls(HueEntsV2.BridgeHome)
    @route("GET", "/resource/bridge_home")
    async def get_bridge_homes(self):
        ...

    @ret_cls(HueEntsV2.BridgeHome)
    @route("GET", "/resource/bridge_home/{bridge_home_id}")
    async def get_bridge_home(self, bridge_home_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/bridge_home/{bridge_home_id}")
    async def set_bridge_home(self, bridge_home_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.GroupedLight)
    @route("GET", "/resource/grouped_light")
    async def get_grouped_lights(self):
        ...

    @ret_cls(HueEntsV2.GroupedLight)
    @route("GET", "/resource/grouped_light/{grouped_light_id}")
    async def get_grouped_light(self, grouped_light_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/grouped_light/{grouped_light_id}")
    async def set_grouped_light(self, grouped_light_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.Device)
    @route("GET", "/resource/device")
    async def get_devices(self):
        ...

    @ret_cls(HueEntsV2.Device)
    @route("GET", "/resource/device/{device_id}")
    async def get_device(self, device_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/device/{device_id}")
    async def set_device(self, device_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.Bridge)
    @route("GET", "/resource/bridges")
    async def get_bridges(self):
        ...

    @ret_cls(HueEntsV2.Bridge)
    @route("GET", "/resource/bridges/{bridge_id}")
    async def get_bridge(self, bridge_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/bridges/{bridge_id}")
    async def set_bridge(self, bridge_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.DevicePower)
    @route("GET", "/resource/device_power")
    async def get_device_powers(self):
        ...

    @ret_cls(HueEntsV2.DevicePower)
    @route("GET", "/resource/device_power/{device_power_id}")
    async def get_device_power(self, device_power_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/device_power/{device_power_id}")
    async def set_device_power(self, device_power_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.ZigbeeConnectivity)
    @route("GET", "/resource/zigbee_connectivity")
    async def get_zigbee_connectivities(self):
        ...

    @ret_cls(HueEntsV2.ZigbeeConnectivity)
    @route("GET", "/resource/zigbee_connectivity/{zigbee_connectivity_id}")
    async def get_zigbee_connectivity(self, zigbee_connectivity_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/zigbee_connectivity/{zigbee_connectivity_id}")
    async def set_zigbee_connectivity(self, zigbee_connectivity_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.ZGPConnectivity)
    @route("GET", "/resource/zgb_connectivity")
    async def get_zgb_connectivities(self):
        ...

    @ret_cls(HueEntsV2.ZGPConnectivity)
    @route("GET", "/resource/zgb_connectivity/{zgb_connectivity_id}")
    async def get_zgb_connectivity(self, zgb_connectivity_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/zgb_connectivity/{zgb_connectivity_id}")
    async def set_zgb_connectivity(self, zgb_connectivity_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.Motion)
    @route("GET", "/resource/motion")
    async def get_motions(self):
        ...

    @ret_cls(HueEntsV2.Motion)
    @route("GET", "/resource/motion/{motion_id}")
    async def get_motion(self, motion_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/motion/{motion_id}")
    async def set_motion(self, motion_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.Temperature)
    @route("GET", "/resource/temperature")
    async def get_temperatures(self):
        ...

    @ret_cls(HueEntsV2.Temperature)
    @route("GET", "/resource/temperature/{temperature_id}")
    async def get_temperature(self, temperature_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/temperature/{temperature_id}")
    async def set_temperature(self, temperature_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.LightLevel)
    @route("GET", "/resource/light_level")
    async def get_light_levels(self):
        ...

    @ret_cls(HueEntsV2.LightLevel)
    @route("GET", "/resource/light_level/{light_level_id}")
    async def get_light_level(self, light_level_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/light_level/{light_level_id}")
    async def set_light_level(self, light_level_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.Button)
    @route("GET", "/resource/button")
    async def get_buttons(self):
        ...

    @ret_cls(HueEntsV2.Button)
    @route("GET", "/resource/button/{button_id}")
    async def get_button(self, button_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/button/{button_id}")
    async def set_button(self, button_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.BehaviorScript)
    @route("GET", "/resource/behavior_script")
    async def get_behavior_scripts(self):
        ...

    @ret_cls(HueEntsV2.BehaviorScript)
    @route("GET", "/resource/behavior_script/{behavior_script_id}")
    async def get_behavior_script(self, behavior_script_id: UUID, /):
        ...

    @ret_cls(HueEntsV2.BehaviorInstance)
    @route("GET", "/resource/behavior_instance")
    async def get_behavior_instances(self):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("POST", "/resource/behavior_instance")
    async def create_behavior_instance(self, **kwargs):
        ...

    @ret_cls(HueEntsV2.BehaviorInstance)
    @route("GET", "/resource/behavior_instance/{behavior_instance_id}")
    async def get_behavior_instance(self, behavior_instance_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/behavior_instance/{behavior_instance_id}")
    async def set_behavior_instance(self, behavior_instance_id: UUID, /, **kwargs):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("DELETE", "/resource/behavior_instance/{behavior_instance_id}")
    async def delete_behavior_instance(self, behavior_instance_id: UUID, /):
        ...

    @ret_cls(HueEntsV2.GeofenceClient)
    @route("GET", "/resource/geofence_client")
    async def get_geofence_clients(self):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("POST", "/resource/geofence_client")
    async def create_geofence_client(self, **kwargs):
        ...

    @ret_cls(HueEntsV2.GeofenceClient)
    @route("GET", "/resource/geofence_client/{geofence_client_id}")
    async def get_geofence_client(self, geofence_client_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/geofence_client/{geofence_client_id}")
    async def set_geofence_client(self, geofence_client_id: UUID, /, **kwargs):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("DELETE", "/resource/geofence_client/{geofence_client_id}")
    async def delete_geofence_client(self, geofence_client_id: UUID, /):
        ...

    @ret_cls(HueEntsV2.Geolocation)
    @route("GET", "/resource/geolocation")
    async def get_geolocations(self):
        ...

    @ret_cls(HueEntsV2.Geolocation)
    @route("GET", "/resource/geolocation/{geolocation_id}")
    async def get_geolocation(self, geolocation_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/geolocation/{geolocation_id}")
    async def set_geolocation(self, geolocation_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.EntertainmentConfiguration)
    @route("GET", "/resource/entertainment_configuration")
    async def get_entertainment_configurations(self):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("POST", "/resource/entertainment_configuration")
    async def create_entertainment_configuration(self, **kwargs):
        ...

    @ret_cls(HueEntsV2.EntertainmentConfiguration)
    @route(
        "GET", "/resource/entertainment_configuration/{entertainment_configuration_id}"
    )
    async def get_entertainment_configuration(
        self,
        entertainment_configuration_id: UUID,
        /,
    ):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route(
        "PUT", "/resource/entertainment_configuration/{entertainment_configuration_id}"
    )
    async def set_entertainment_configuration(
        self, entertainment_configuration_id: UUID, /, **kwargs
    ):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route(
        "DELETE",
        "/resource/entertainment_configuration/{entertainment_configuration_id}",
    )
    async def delete_entertainment_configuration(
        self,
        entertainment_configuration_id: UUID,
        /,
    ):
        ...

    @ret_cls(HueEntsV2.Entertainment)
    @route("GET", "/resource/entertainment")
    async def get_entertainments(self):
        ...

    @ret_cls(HueEntsV2.Entertainment)
    @route("GET", "/resource/entertainment/{entertainment_id}")
    async def get_entertainment(self, entertainment_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/entertainment/{entertainment_id}")
    async def set_entertainment(self, entertainment_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.Homekit)
    @route("GET", "/resource/homekit")
    async def get_homekits(self):
        ...

    @ret_cls(HueEntsV2.Homekit)
    @route("GET", "/resource/homekit/{homekit_id}")
    async def get_homekit(self, homekit_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/homekit/{homekit_id}")
    async def set_homekit(
        self,
        homekit_id: UUID,
        /,
        type: Optional[str] = None,
        action: Optional[Literal["homekit_reset"]] = None,
    ):
        ...

    @ret_cls(HueEntsV2.Resource)
    @route("GET", "/resource")
    async def get_resources(self):
        ...

    @route("GET", "../../eventstream/clip/v2")
    async def listen_events(self):
        ...

    @ret_cls(HueEntsV2.RelativeRotary)
    @route("GET", "/resource/relative_rotary")
    async def get_rotaries(self):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("PUT", "/resource/relative_rotary/{relative_rotary_id}")
    async def set_rotary(self, relative_rotary_id: UUID, /, **kwargs):
        ...

    @ret_cls(HueEntsV2.RelativeRotary)
    @route("GET", "/resource/relative_rotary/{relative_rotary_id}")
    async def get_rotary(self, relative_rotary_id: UUID, /):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("POST", "/resource/relative_rotary")
    async def create_rotary(self, **kwargs):
        ...

    @ret_cls(models.Attributes.Identifier)
    @route("DELETE", "/resource/relative_rotary/{relative_rotary_id}")
    async def delete_rotary(self, relative_rotary_id: UUID, /):
        ...

    @abstractmethod
    async def on_motion_update(self, motion: HueEntsV2.Motion):
        ...

    @abstractmethod
    async def on_button_update(self, button: HueEntsV2.Button):
        ...

    @abstractmethod
    async def on_zone_update(self, zone: HueEntsV2.Zone):
        ...

    @abstractmethod
    async def on_zigbee_connectivity_update(self, zigbee: HueEntsV2.ZigbeeConnectivity):
        ...

    @abstractmethod
    async def on_zgp_connectivity_update(
        self, zgp_connectivity: HueEntsV2.ZGPConnectivity
    ):
        ...

    @abstractmethod
    async def on_temperature_update(self, temperature: HueEntsV2.Temperature):
        ...

    @abstractmethod
    async def on_scene_update(self, scene: HueEntsV2.Scene):
        ...

    @abstractmethod
    async def on_room_update(self, room: HueEntsV2.Room):
        ...

    @abstractmethod
    async def on_resource_update(self, device: HueEntsV2.Resource):
        ...

    @abstractmethod
    async def on_relative_rotary_update(
        self, relative_rotary: HueEntsV2.RelativeRotary
    ):
        ...

    @abstractmethod
    async def on_light_level_update(self, light_level: HueEntsV2.LightLevel):
        ...

    @abstractmethod
    async def on_light_update(self, light: HueEntsV2.Light):
        ...

    @abstractmethod
    async def on_homekit_update(self, homekit: HueEntsV2.Homekit):
        ...

    @abstractmethod
    async def on_grouped_light_update(self, grouped_light: HueEntsV2.GroupedLight):
        ...

    @abstractmethod
    async def on_geolocation_update(self, geolocation: HueEntsV2.Geolocation):
        ...

    @abstractmethod
    async def on_geofence_client_update(
        self, geofence_client: HueEntsV2.GeofenceClient
    ):
        ...

    @abstractmethod
    async def on_entertainment_configuration_update(
        self, entertainment_configuration: HueEntsV2.EntertainmentConfiguration
    ):
        ...

    @abstractmethod
    async def on_entertainment_update(self, entertainment: HueEntsV2.Entertainment):
        ...

    @abstractmethod
    async def on_device_power_update(self, device_power: HueEntsV2.DevicePower):
        ...

    @abstractmethod
    async def on_device_update(self, device: HueEntsV2.Device):
        ...

    @abstractmethod
    async def on_bridge_home_update(self, bridge_home: HueEntsV2.BridgeHome):
        ...

    @abstractmethod
    async def on_bridge_update(self, bridge: HueEntsV2.Bridge):
        ...

    @abstractmethod
    async def on_behavior_script_update(
        self, behavior_script: HueEntsV2.BehaviorScript
    ):
        ...

    @abstractmethod
    async def on_behavior_instance_update(
        self, behavior_instance: HueEntsV2.BehaviorInstance
    ):
        ...


class Router(HueAPIv2):
    def __new__(cls, hue_api_key: str, bridge_ip: str = "", max_cache_size: int = 10):
        cls = super().__new__(cls, hue_api_key)
        return cls

    def __init__(
        self,
        hue_api_key: Optional[str] = None,
        bridge_ip: Optional[str] = None,
        max_cache_size=10,
    ):
        with open("config.yaml", "r+") as f:
            self.config = load(f, Loader=Loader)
        super().__init__(hue_api_key or self.config.api_key)
        self.cache = LRU(max_cache_size)
        self._client = AsyncClient(headers=self._headers, verify=False)
        self._subscription = None
        self._bridge_ip = bridge_ip or self.config.bridge_ip
        self._tasks = []
        self.lights = {}
        self.bridges = {}
        self.entertainment_configurations = {}
        self.entertainments = {}
        self.buttons = {}
        self.rooms = {}
        self.scenes = {}
        self.zones = {}
        self.rotaries = {}
        self.geofences = {}
        self.behavior_instances = {}
        self.bridge_homes = {}
        self.zgb_connectivities = {}
        self.zigbee_connectivities = {}

    def subscribe(self, *args, **kwargs):
        if not self._subscription or self._subscription.done():
            self._subscription = self.new_task(self._subscribe(*args, **kwargs))

    def run(self):
        loop = new_event_loop()
        try:
            loop.run_until_complete(self._startup())
            loop.run_forever()
        except KeyboardInterrupt:
            for t in self._tasks:
                t.cancel()
            for t in self.cache:
                t.value.cancel()
            print("Exiting..")
            loop.stop()
            loop.close()

    def new_task(self, coro):
        self._tasks.append(t := get_running_loop().create_task(coro))
        return t

    async def _startup(self):
        try:
            loop = get_running_loop()
            for k, v in self.config["aliases"].items():
                fn = getattr(self, f"get_{k}")
                objs = await fn()
                for obj in objs:
                    alias = v.get(str(obj.id))
                    if alias:
                        ob = obj.__class__(id=obj.id)
                        getattr(self, k)[alias] = ob
                        setattr(self, alias, ob)

            self.new_task(self._subscribe())

            while loop.is_running():
                await sleep(60)
        except KeyboardInterrupt:
            await gather(*self._tasks)

    def _parse_payload(self, payload: bytes):
        _match = MSG_RE_BYTES.search(payload)
        if not _match:
            return None
        _events, _data, _id = [], b"", b""
        if (_data := _match.group("data")) and (_id := _match.group("id")):
            _events.extend(loads(_data))

        for _event in _events:
            for _ent in _event["data"]:
                _event_id = _id.decode()
                _event_type = _event["type"]
                _object = TYPE_CACHE[_ent["type"]](**_ent)
                event = Event(
                    id=_event_id,
                    object=_object,
                    type=_event_type,
                )

                if hasattr(self, f"on_{event.object.type}_{event.type}"):
                    self.cache.add(
                        get_running_loop().create_task(
                            getattr(self, f"on_{event.object.type}_{event.type}")(
                                _object
                            )
                        )
                    )

    async def _subscribe(self, *args, **kwargs):
        if hasattr(self, "on_ready"):
            self.new_task(self.on_ready())
        while get_running_loop().is_running():
            try:
                stream = await self.listen_events(
                    headers={**self._headers, **{"Accept": "text/event-stream"}}
                )
                async with stream as _iter:
                    async for msg in _iter.aiter_bytes():
                        self._parse_payload(msg)

            except (ReadTimeout, HTTPxReadTimeout, ConnectTimeout, ConnectError):
                ...
            await sleep(1)
