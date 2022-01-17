"""Summary."""
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Union

import jsons
import pydash

from ergo.stack import Stack

DATA_KEY = "data"


@dataclass
class Payload:
    data: Any = field(default=None)
    key: Optional[str] = None
    log: List = field(default_factory=list)
    stack: Optional[Stack] = None
    error: Optional[Dict[str, str]] = None
    traceback: Optional[str] = None

    def get(self, key: str, default=None):
        value = pydash.get(self.data, key)
        if value:
            return value
        if key == DATA_KEY:
            return self.data
        return default


def decodes(s: str) -> Payload:
    return decode(**jsons.loads(s))


def decode(data=None, **kwargs) -> Payload:
    # if `data` is non-null, assume this payload was sent by an upstream component, and the other kwargs are metadata
    # otherwise, assume this payload came from outside of ergo, and bind all kwargs to `data`.
    return jsons.load({"data": data or kwargs, **kwargs}, cls=Payload)


def encodes(data: Union[Payload, Iterable[Payload]]) -> str:
    return jsons.dumps(data)
