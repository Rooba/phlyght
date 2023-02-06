from collections import deque
from inspect import Parameter, signature
from typing import Any
from time import time

from re import compile as re_compile

from httpx._urls import URL as _URL
from pydantic import BaseModel, Field


try:
    from ujson import dumps, loads, JSONDecodeError
except ImportError:
    try:
        from orjson import dumps, loads, JSONDecodeError
    except ImportError:
        from json import dumps, loads, JSONDecodeError

try:
    from yarl import URL as UR
except ImportError:
    ...

__all__ = (
    "ENDPOINT_METHOD",
    "STR_FMT_RE",
    "URL_TYPES",
    "IP_RE",
    "MSG_RE_BYTES",
    "MSG_RE_TEXT",
    "URL",
    "LRU",
    "LRUItem",
    "get_url_args",
    "get_data_fields",
    "ret_cls",
)

ENDPOINT_METHOD = re_compile(r"^(?=((?:get|set|create|delete)\w+))\1")
STR_FMT_RE = re_compile(r"(?=(\{([^:]+)(?::([^}]+))?\}))\1")
URL_TYPES = {"str": str, "int": int}
IP_RE = re_compile(
    r"(?=(?:(?<=[^0-9])|^)((?:[a-z0-9]+\.)*[a-z0-9]+\.[a-z]{2,}(?:[0-9]{2,5})?|(?:[0-9]{,3}\.){3}[0-9]{,3}))\1"
)

MSG_RE_BYTES = re_compile(
    rb"(?=((?P<hello>^: hi\n\n$)|^id:\s(?P<id>[0-9]+:\d*?)\ndata:(?P<data>[^$]+)\n\n))\1"
)
MSG_RE_TEXT = re_compile(
    r"(?=((?P<hello>^: hi\n\n$)|^id:\s(?P<id>[0-9]+:\d*?)\ndata:(?P<data>[^$]+)\n\n))\1"
)


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


def get_data_fields(fn, data, args, kwargs) -> dict[str, Any]:
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
    return data


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
                ret = ret.get("data", None)
                _rets = []

                if not ret:
                    return []

                if isinstance(ret, list):
                    for r in ret:
                        _rets.append(cls(**r))
                else:
                    return cls(**ret)

                return _rets
            except JSONDecodeError:
                return []

        return sub_wrap

    wrapped.__return_type__ = cls

    return wrapped


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
        self.items = deque(maxlen=maxsize)
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
