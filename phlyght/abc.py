from typing import Any
from httpx import AsyncClient

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
