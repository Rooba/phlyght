__all__ = ("Router", "route", "RouterMeta", "SubRouter", "HughApi")

from asyncio import get_running_loop, sleep
from inspect import signature
from re import compile
from typing import Any, Literal, Optional
from uuid import UUID
from time import time

from httpx import AsyncClient
from httpx._urls import URL as _URL
from httpcore._exceptions import ReadTimeout
from attrs import define, field
from json import loads
from pydantic import BaseModel


try:
    from yarl import URL as UR
except ImportError:
    ...

try:
    from rich import print  # noqa
except ImportError:
    ...

from . import models


STR_FMT_RE = compile(r"""(?=(\{([^:]+)(?::([^}]+))?\}))\1""")
URL_TYPES = {"str": str, "int": int}
IP_RE = compile(r"(?=(?:(?<=[^0-9])|)((?:[0-9]{,3}\.){3}[0-9]{,3}))\1")

MSG_RE = compile(
    b"""(?=((?P<hello>^hi\\n\\n$)|^id:\\s(?P<id>[0-9]+:\\d*?)\\ndata:(?P<data>[^$]+)\\n\\n))\\1"""
)
TYPE_CACHE = {}

for k in models.__all__:
    if (
        k == "Literal"
        or k.startswith("_")
        or not issubclass(getattr(models, k), BaseModel)
    ):
        continue
    TYPE_CACHE[getattr(models, k).__fields__["type"].default] = getattr(models, k)


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


@define
class LRUItem:
    access_time: int = field(init=False, factory=lambda: int(time()))
    value: Any = object

    def __id__(self):
        return id(self.value.id)

    def __hash__(self):
        return hash(self.value.id)


class LRU(set):
    def __init__(self, *items, maxsize=128):
        self.maxsize = maxsize
        super().__init__()
        for item in items[:maxsize]:
            self.add(LRUItem(value=item))

    def add(self, item):
        if len(self) + 1 > self.maxsize:
            self ^= set(
                sorted(self, key=lambda x: x.access_time)[
                    : len(self) + 1 - self.maxsize
                ]
            )

        super().add(LRUItem(value=item))

    def pop(self):
        super().pop().value

    def remove(self, item):
        super().remove(*filter(lambda x: x.value == item, self))

    def extend(self, *items):
        len_new = len(self) + len(items)
        if len_new > self.maxsize:
            self ^= set(
                sorted(self, key=lambda x: x.access_time)[: len_new - self.maxsize]
            )
        self |= set([LRUItem(value=item) for item in items])


class URL(_URL):
    def __truediv__(self, other):
        # Why am i doing this? good question.
        try:
            return URL(str(UR(f"{self}") / other.lstrip("/")))
        except NameError:
            return URL(str(f"{self}/{other.lstrip('/')}"))

    def __floordiv__(self, other):
        try:
            return URL(str(UR(f"{self}") / other.lstrip("/")))
        except NameError:
            return URL(str(f"{self}/{other.lstrip('/')}"))


def ret_cls(cls):
    def wrapped(fn):
        async def sub_wrap(self, *args, **kwargs):
            kwargs.pop("base_uri", None)
            ret = (await fn(self, *args, **kwargs)).json().get("data", [])
            _rets = []

            if isinstance(ret, list):
                for r in ret:
                    _rets.append(cls(**r))
            else:
                return cls(**ret)
            return _rets

        return sub_wrap

    return wrapped


def route(method, endpoint) -> Any:
    def wrapped(fn):
        async def sub_wrap(
            self: "SubRouter",
            base_uri=None,
            content: Optional[bytes] = None,
            data: Optional[dict[str, str]] = None,
            params: Optional[dict[str, str]] = None,
            **kwargs,
        ):
            params = params or {}
            data = data or {}
            if "headers" in kwargs:
                headers = kwargs.pop("headers")
            else:
                headers = None
            for param_name, param in signature(fn).parameters.items():
                if param_name == "self":
                    continue

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
                    if kwargs.get(param_name, None):
                        data[param_name] = type_(kwargs.pop(param_name))

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

            _url_base = f"https://{_match_bridge.group(1)}/{base_uri}"
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
                return await self._client.request(
                    method,
                    new_endpoint,
                    content=content,
                    data=data,
                    params=params,
                    headers=headers,
                )

        return sub_wrap

    return wrapped


class RouterMeta(type):
    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        if bases:
            return kwargs | bases[0].__dict__
        return kwargs

    def __new__(cls, name, bases, kwds, **kwargs):
        cells = {}
        _base = kwds.get("BASE_URI", "")

        def set_key(v):
            def wrap(self, *args, **_kwds):
                return v(self, *args, base_uri=_base, **_kwds)

            return wrap

        if any(map(lambda x: not x.startswith("__"), kwds.keys())):
            funcs = list(
                filter(
                    lambda k: not k[0].startswith("__") and callable(k[1]), kwds.items()
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

    def __init_subclass__(cls, *args, **kwargs) -> None:
        super().__init_subclass__()
        if kwargs.get("root"):
            cls._api_path = f'{kwargs.get("root")}{cls.BASE_URI}'


class HughApi(SubRouter):
    BASE_URI = "/clip/v2"

    @ret_cls(models.Light)
    @route("GET", "/resource/light")
    async def get_lights(self, friendly_name: Optional[str] = None):
        ...

    @ret_cls(models.Light)
    @route("GET", "/resource/light/{light_id}")
    async def get_light(self, light_id: str):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/light/{light_id}")
    async def set_light(
        self,
        light_id: int,
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

    @ret_cls(models.Scene)
    @route("GET", "/resource/scene")
    async def get_scenes(self):
        ...

    @ret_cls(models.Identifier)
    @route("POST", "/resource/scene")
    async def create_scene(self, **kwargs):
        ...

    @ret_cls(models.Scene)
    @route("GET", "/resource/scene/{scene_id}")
    async def get_scene(self, scene_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/scene/{scene_id}")
    async def set_scene(self, scene_id: UUID, **kwargs):
        ...

    @ret_cls(models.Identifier)
    @route("DELETE", "/resource/scene/{scene_id}")
    async def delete_scene(self, scene_id: UUID):
        ...

    @ret_cls(models.Room)
    @route("GET", "/resource/room")
    async def get_rooms(self):
        ...

    @ret_cls(models.Identifier)
    @route("POST", "/resource/room")
    async def create_room(self, **kwargs):
        ...

    @ret_cls(models.Room)
    @route("GET", "/resource/room/{room_id}")
    async def get_room(self, room_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/room/{room_id}")
    async def set_room(
        self,
        room_id: UUID,
        metadata: Optional[dict[str, str]] = None,
        children: Optional[models.Identifier] = None,
    ):
        ...

    @ret_cls(models.Identifier)
    @route("DELETE", "/resource/room/{room_id}")
    async def delete_room(self, room_id: UUID):
        ...

    @ret_cls(models.Zone)
    @route("GET", "/resource/zone")
    async def get_zones(self):
        ...

    @ret_cls(models.Identifier)
    @route("POST", "/resource/zone")
    async def create_zone(self, **kwargs):
        ...

    @ret_cls(models.Zone)
    @route("GET", "/resource/zone/{zone_id}")
    async def get_zone(self, zone_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/zone/{zone_id}")
    async def set_zone(self, zone_id: UUID, **kwargs):
        ...

    @ret_cls(models.Identifier)
    @route("DELETE", "/resource/zone/{zone_id}")
    async def delete_zone(self, zone_id: UUID):
        ...

    @ret_cls(models.BridgeHome)
    @route("GET", "/resource/bridge_home")
    async def get_bridge_homes(self):
        ...

    @ret_cls(models.BridgeHome)
    @route("GET", "/resource/bridge_home/{bridge_home_id}")
    async def get_bridge_home(self, bridge_home_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/bridge_home/{bridge_home_id}")
    async def set_bridge_home(self, bridge_home_id: UUID, **kwargs):
        ...

    @ret_cls(models.GroupedLight)
    @route("GET", "/resource/grouped_light")
    async def get_grouped_lights(self):
        ...

    @ret_cls(models.GroupedLight)
    @route("GET", "/resource/grouped_light/{grouped_light_id}")
    async def get_grouped_light(self, grouped_light_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/grouped_light/{grouped_light_id}")
    async def set_grouped_light(self, grouped_light_id: UUID, **kwargs):
        ...

    @ret_cls(models.Device)
    @route("GET", "/resource/device")
    async def get_devices(self):
        ...

    @ret_cls(models.Device)
    @route("GET", "/resource/device/{device_id}")
    async def get_device(self, device_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/device/{device_id}")
    async def set_device(self, device_id: UUID, **kwargs):
        ...

    @ret_cls(models.Bridge)
    @route("GET", "/resource/bridges")
    async def get_bridges(self):
        ...

    @ret_cls(models.Bridge)
    @route("GET", "/resource/bridges/{bridge_id}")
    async def get_bridge(self, bridge_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/bridges/{bridge_id}")
    async def set_bridge(self, bridge_id: UUID, **kwargs):
        ...

    @ret_cls(models.DevicePower)
    @route("GET", "/resource/device_power")
    async def get_device_powers(self):
        ...

    @ret_cls(models.DevicePower)
    @route("GET", "/resource/device_power/{device_power_id}")
    async def get_device_power(self, device_power_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/device_power/{device_power_id}")
    async def set_device_power(self, device_power_id: UUID, **kwargs):
        ...

    @ret_cls(models.ZigbeeConnectivity)
    @route("GET", "/resource/zigbee_connectivity")
    async def get_zigbee_connectivities(self):
        ...

    @ret_cls(models.ZigbeeConnectivity)
    @route("GET", "/resource/zigbee_connectivity/{zigbee_connectivity_id}")
    async def get_zigbee_connectivity(self, zigbee_connectivity_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/zigbee_connectivity/{zigbee_connectivity_id}")
    async def set_zigbee_connectivity(self, zigbee_connectivity_id: UUID, **kwargs):
        ...

    @ret_cls(models.ZGPConnectivity)
    @route("GET", "/resource/zgb_connectivity")
    async def get_zgb_connectivities(self):
        ...

    @ret_cls(models.ZGPConnectivity)
    @route("GET", "/resource/zgb_connectivity/{zgb_connectivity_id}")
    async def get_zgb_connectivity(self, zgb_connectivity_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/zgb_connectivity/{zgb_connectivity_id}")
    async def set_zgb_connectivity(self, zgb_connectivity_id: UUID, **kwargs):
        ...

    @ret_cls(models.Motion)
    @route("GET", "/resource/motion")
    async def get_motions(self):
        ...

    @ret_cls(models.Motion)
    @route("GET", "/resource/motion/{motion_id}")
    async def get_motion(self, motion_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/motion/{motion_id}")
    async def set_motion(self, motion_id: UUID, **kwargs):
        ...

    @ret_cls(models.Temperature)
    @route("GET", "/resource/temperature")
    async def get_temperatures(self):
        ...

    @ret_cls(models.Temperature)
    @route("GET", "/resource/temperature/{temperature_id}")
    async def get_temperature(self, temperature_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/temperature/{temperature_id}")
    async def set_temperature(self, temperature_id: UUID, **kwargs):
        ...

    @ret_cls(models.LightLevel)
    @route("GET", "/resource/light_level")
    async def get_light_levels(self):
        ...

    @ret_cls(models.LightLevel)
    @route("GET", "/resource/light_level/{light_level_id}")
    async def get_light_level(self, light_level_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/light_level/{light_level_id}")
    async def set_light_level(self, light_level_id: UUID, **kwargs):
        ...

    @ret_cls(models.Button)
    @route("GET", "/resource/button")
    async def get_buttons(self):
        ...

    @ret_cls(models.Button)
    @route("GET", "/resource/button/{button_id}")
    async def get_button(self, button_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/button/{button_id}")
    async def set_button(self, button_id: UUID, **kwargs):
        ...

    @ret_cls(models.BehaviorScript)
    @route("GET", "/resource/behavior_script")
    async def get_behavior_scripts(self):
        ...

    @ret_cls(models.BehaviorScript)
    @route("GET", "/resource/behavior_script/{behavior_script_id}")
    async def get_behavior_script(self, behavior_script_id: UUID):
        ...

    @ret_cls(models.BehaviorInstance)
    @route("GET", "/resource/behavior_instance")
    async def get_behavior_instances(self):
        ...

    @ret_cls(models.Identifier)
    @route("POST", "/resource/behavior_instance")
    async def create_behavior_instance(self, **kwargs):
        ...

    @ret_cls(models.BehaviorInstance)
    @route("GET", "/resource/behavior_instance/{behavior_instance_id}")
    async def get_behavior_instance(self, behavior_instance_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/behavior_instance/{behavior_instance_id}")
    async def set_behavior_instance(self, behavior_instance_id: UUID, **kwargs):
        ...

    @ret_cls(models.Identifier)
    @route("DELETE", "/resource/behavior_instance/{behavior_instance_id}")
    async def delete_behavior_instance(self, behavior_instance_id: UUID):
        ...

    @ret_cls(models.GeofenceClient)
    @route("GET", "/resource/geofence_client")
    async def get_geofence_clients(self):
        ...

    @ret_cls(models.Identifier)
    @route("POST", "/resource/geofence_client")
    async def create_geofence_client(self, **kwargs):
        ...

    @ret_cls(models.GeofenceClient)
    @route("GET", "/resource/geofence_client/{geofence_client_id}")
    async def get_geofence_client(self, geofence_client_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/geofence_client/{geofence_client_id}")
    async def set_geofence_client(self, geofence_client_id: UUID, **kwargs):
        ...

    @ret_cls(models.Identifier)
    @route("DELETE", "/resource/geofence_client/{geofence_client_id}")
    async def delete_geofence_client(self, geofence_client_id: UUID):
        ...

    @ret_cls(models.Geolocation)
    @route("GET", "/resource/geolocation")
    async def get_geolocations(self):
        ...

    @ret_cls(models.Geolocation)
    @route("GET", "/resource/geolocation/{geolocation_id}")
    async def get_geolocation(self, geolocation_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/geolocation/{geolocation_id}")
    async def set_geolocation(self, geolocation_id: UUID, **kwargs):
        ...

    @ret_cls(models.EntertainmentConfiguration)
    @route("GET", "/resource/entertainment_configuration")
    async def get_entertainment_configurations(self):
        ...

    @ret_cls(models.Identifier)
    @route("POST", "/resource/entertainment_configuration")
    async def create_entertainment_configuration(self, **kwargs):
        ...

    @ret_cls(models.EntertainmentConfiguration)
    @route(
        "GET", "/resource/entertainment_configuration/{entertainment_configuration_id}"
    )
    async def get_entertainment_configuration(
        self, entertainment_configuration_id: UUID
    ):
        ...

    @ret_cls(models.Identifier)
    @route(
        "PUT", "/resource/entertainment_configuration/{entertainment_configuration_id}"
    )
    async def set_entertainment_configuration(
        self, entertainment_configuration_id: UUID, **kwargs
    ):
        ...

    @ret_cls(models.Identifier)
    @route(
        "DELETE",
        "/resource/entertainment_configuration/{entertainment_configuration_id}",
    )
    async def delete_entertainment_configuration(
        self, entertainment_configuration_id: UUID
    ):
        ...

    @ret_cls(models.Entertainment)
    @route("GET", "/resource/entertainment")
    async def get_entertainments(self):
        ...

    @ret_cls(models.Entertainment)
    @route("GET", "/resource/entertainment/{entertainment_id}")
    async def get_entertainment(self, entertainment_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/entertainment/{entertainment_id}")
    async def set_entertainment(self, entertainment_id: UUID, **kwargs):
        ...

    @ret_cls(models.Homekit)
    @route("GET", "/resource/homekit")
    async def get_homekits(self):
        ...

    @ret_cls(models.Homekit)
    @route("GET", "/resource/homekit/{homekit_id}")
    async def get_homekit(self, homekit_id: UUID):
        ...

    @ret_cls(models.Identifier)
    @route("PUT", "/resource/homekit/{homekit_id}")
    async def set_homekit(
        self,
        homekit_id: UUID,
        type: Optional[str] = None,
        action: Optional[Literal["homekit_reset"]] = None,
    ):
        ...

    @ret_cls(models.Resource)
    @route("GET", "/resource")
    async def get_resources(self):
        ...

    @route("GET", "/../../eventstream/clip/v2")
    async def listen_events(self):
        ...


class Router(HughApi):
    def __new__(cls, hue_api_key: str, bridge_ip: str = "", max_cache_size: int = 512):
        cls = super().__new__(cls, hue_api_key)
        return cls

    def __init__(
        self, hue_api_key: str, bridge_ip: Optional[str] = None, max_cache_size=512
    ):
        super().__init__(hue_api_key)
        self._client = AsyncClient(headers=self._headers, verify=False)
        self._subscription = None
        self._bridge_ip = bridge_ip or ""
        self.cache = LRU(maxsize=max_cache_size)

    def subscribe(self, *args, **kwargs):
        if not self._subscription or self._subscription.done():
            self._subscription = get_running_loop().create_task(self._subscribe())

    async def _subscribe(self, *args, **kwargs):

        stream = await self.listen_events(
            headers={"Accept": "text/event-stream"} | self._headers
        )
        while get_running_loop().is_running():
            resp = await stream.gen.__anext__()
            _bound = resp.stream._stream._httpcore_stream
            try:
                async for msg in _bound:
                    payload = []
                    _match = MSG_RE.search(msg)
                    id_ = ""
                    if _match:
                        if _match.groupdict().get("hello", None):
                            #  Handshake / Heartbeat
                            ...
                        else:
                            payload = loads(_match.group("data"))
                            id_ = _match.group("id")

                    for event in payload:
                        for ob in event["data"]:
                            self.cache.add(TYPE_CACHE[ob["type"]](**ob))

                    print(len(self.cache))

            except ReadTimeout:
                stream = await self.listen_events(
                    headers={"Accept": "text/event-stream"} | self._headers
                )