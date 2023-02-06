from typing import Any, Optional, Self
from httpx import AsyncClient
from yaml import YAMLObject

from .utils import ENDPOINT_METHOD


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
    _bridge_host: str

    def __new__(cls, **kwargs):
        if not hasattr(cls, "handlers"):
            cls.handlers: dict[str, type] = {}

        for base in cls.__bases__:
            if hasattr(base, "handlers"):
                cls.handlers |= getattr(base, "handlers")

        return super().__new__(cls)

    def __init__(self, api_key: str, /):
        self._api_key = api_key
        self._headers = {
            "User-Agent": "Python/HueClient",
            "hue-application-key": self._api_key,
        }

    def __init_subclass__(cls, *_, **kwargs) -> None:
        super().__init_subclass__()
        if kwargs.get("root"):
            cls._api_path = f'{kwargs.get("root")}{cls.BASE_URI}'

    def __getattribute__(self, key) -> Any:
        return object.__getattribute__(self, key)


class YAMLConfig(YAMLObject, dict):
    yaml_tag = "!YAMLConfig"

    def __setstate__(self, state):
        for k, v in state.items():
            if isinstance(v, dict):
                v = YAMLConfig(**v)

            setattr(self, k, v)
            dict.__setitem__(self, k, v)
            self.__dict__[k] = v

        return self

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = YAMLConfig(**value)

        dict.__setitem__(self, key, value)
        setattr(self, key, value)
        self.__dict__[key] = value

    def __getattribute__(self, name):
        return object.__getattribute__(self, name)

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def keys(self):
        return dict.keys(self)

    def __iter__(self):
        return dict.__iter__(self)

    def __get__(self, key, f=None) -> Self | Any | None:
        if f:
            return self
        return getattr(self, key, None)

    def __init__(self, **data):
        super().__init__()
        for k, v in data.items():
            self.__dict__[k] = v
            self.__setattr__(k, v)
            dict.__setitem__(self, k, v)

    def items(self):
        return dict.items(self)

    def __repr__(self):
        return dict.__repr__(self)

    def __str__(self):
        return dict.__str__(self)
