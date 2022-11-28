__all__ = ("Router", "route", "RouterMeta", "SubRouter", "HughApi")

from inspect import signature
from re import compile
from typing import Any, Literal, Optional
from uuid import UUID

from httpx import AsyncClient
from httpx._urls import URL as _URL

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
                    print(r)
                    _rets.append(cls(**r))
            else:
                return cls(**ret)
            return _rets

        return sub_wrap

    return wrapped


def route(method, endpoint) -> Any:
    def wrapped(fn):
        async def sub_wrap(
            self: SubRouter,
            base_uri=None,
            content: Optional[bytes] = None,
            data: Optional[dict[str, str]] = None,
            params: Optional[dict[str, str]] = None,
            **kwargs,
        ):
            params = params or {}
            data = data or {}
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

            if url_args:
                new_endpoint = URL(f"{self._api_path}") / endpoint.format(**url_args)
            else:
                new_endpoint = URL(f"{self._api_path}") / endpoint

            return await self._client.request(
                method,
                new_endpoint,
                content=content,
                data=data,
                params=params,
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
        _root = kwargs.get("root", "")
        _base = kwds.get("BASE_URI", "")
        _api = f"{_root}{_base}"

        def set_key(v, base_uri=None):
            def wrap(self, *args, **_kwds):
                return v(self, *args, base_uri=base_uri, **_kwds)

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
                    cells[k] = set_key(v, base_uri=_api)

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

    def __new__(cls, hue_api_key: str):
        if not hasattr(cls, "handlers"):
            cls.handlers = {}

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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
    @route("POST", "/resource/scene")
    async def create_scene(self, **kwargs):
        ...

    @ret_cls(models.Scene)
    @route("GET", "/resource/scene/{scene_id}")
    async def get_scene(self, scene_id: UUID):
        ...

    @ret_cls(models._Identifier)
    @route("PUT", "/resource/scene/{scene_id}")
    async def set_scene(self, scene_id: UUID, **kwargs):
        ...

    @ret_cls(models._Identifier)
    @route("DELETE", "/resource/scene/{scene_id}")
    async def delete_scene(self, scene_id: UUID):
        ...

    @ret_cls(models.Room)
    @route("GET", "/resource/room")
    async def get_rooms(self):
        ...

    @ret_cls(models._Identifier)
    @route("POST", "/resource/room")
    async def create_room(self, **kwargs):
        ...

    @ret_cls(models.Room)
    @route("GET", "/resource/room/{room_id}")
    async def get_room(self, room_id: UUID):
        ...

    @ret_cls(models._Identifier)
    @route("PUT", "/resource/room/{room_id}")
    async def set_room(
        self,
        room_id: UUID,
        metadata: Optional[dict[str, str]] = None,
        children: Optional[models._Identifier] = None,
    ):
        ...

    @ret_cls(models._Identifier)
    @route("DELETE", "/resource/room/{room_id}")
    async def delete_room(self, room_id: UUID):
        ...

    @ret_cls(models.Zone)
    @route("GET", "/resource/zone")
    async def get_zones(self):
        ...

    @ret_cls(models._Identifier)
    @route("POST", "/resource/zone")
    async def create_zone(self, **kwargs):
        ...

    @ret_cls(models.Zone)
    @route("GET", "/resource/zone/{zone_id}")
    async def get_zone(self, zone_id: UUID):
        ...

    @ret_cls(models._Identifier)
    @route("PUT", "/resource/zone/{zone_id}")
    async def set_zone(self, zone_id: UUID, **kwargs):
        ...

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
    @route("POST", "/resource/behavior_instance")
    async def create_behavior_instance(self, **kwargs):
        ...

    @ret_cls(models.BehaviorInstance)
    @route("GET", "/resource/behavior_instance/{behavior_instance_id}")
    async def get_behavior_instance(self, behavior_instance_id: UUID):
        ...

    @ret_cls(models._Identifier)
    @route("PUT", "/resource/behavior_instance/{behavior_instance_id}")
    async def set_behavior_instance(self, behavior_instance_id: UUID, **kwargs):
        ...

    @ret_cls(models._Identifier)
    @route("DELETE", "/resource/behavior_instance/{behavior_instance_id}")
    async def delete_behavior_instance(self, behavior_instance_id: UUID):
        ...

    @ret_cls(models.GeofenceClient)
    @route("GET", "/resource/geofence_client")
    async def get_geofence_clients(self):
        ...

    @ret_cls(models._Identifier)
    @route("POST", "/resource/geofence_client")
    async def create_geofence_client(self, **kwargs):
        ...

    @ret_cls(models.GeofenceClient)
    @route("GET", "/resource/geofence_client/{geofence_client_id}")
    async def get_geofence_client(self, geofence_client_id: UUID):
        ...

    @ret_cls(models._Identifier)
    @route("PUT", "/resource/geofence_client/{geofence_client_id}")
    async def set_geofence_client(self, geofence_client_id: UUID, **kwargs):
        ...

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
    @route("PUT", "/resource/geolocation/{geolocation_id}")
    async def set_geolocation(self, geolocation_id: UUID, **kwargs):
        ...

    @ret_cls(models.EntertainmentConfiguration)
    @route("GET", "/resource/entertainment_configuration")
    async def get_entertainment_configurations(self):
        ...

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
    @route(
        "PUT", "/resource/entertainment_configuration/{entertainment_configuration_id}"
    )
    async def set_entertainment_configuration(
        self, entertainment_configuration_id: UUID, **kwargs
    ):
        ...

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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

    @ret_cls(models._Identifier)
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


class Router(HughApi, root="https://192.168.69.104"):
    def __init__(self, hue_api_key: str):
        super().__init__(hue_api_key)
        self._client = AsyncClient(headers=self._headers, verify=False)
