"""Summary."""
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Union

import jsons
import pydash

from ergo.transaction import Stack

DATA_KEY = "data"


@dataclass
class Metadata:
    key: Optional[str] = None
    log: List = field(default_factory=list)
    stack: Stack = field(default_factory=Stack)
    error: Optional[Dict[str, str]] = None
    traceback: Optional[str] = None


@dataclass
class Payload:
    data: Any = field(default=None)
    metadata: Metadata = field(default_factory=Metadata)

    def get(self, key: str, default=None):
        value = pydash.get(self.data, key)
        if value:
            return value
        if key == DATA_KEY:
            return self.data
        return default


def decodes(s: str) -> Payload:
    return decode(**jsons.loads(s))


def decode(data=None, metadata=None, **kwargs) -> Payload:
    # TODO after all messages written with the old schema have been consumed
    # return jsons.load({"data": data or kwargs, "metadata": metadata or {}}, cls=Payload)

    if data:
        # assume data and metadata are already normalized (sent by an upstream component)
        # metadata in its own key means it was written with the new schema {"data": None, "key": "my_key", ...}
        # metadata in unpacked kwargs means it was written with the old deprecated schema {"data": None, "metadata": {"key": "my_key", ...}}
        metadata = metadata or kwargs
    else:
        # assume _contents is un-normalized (not sent by a component)
        data = kwargs
        metadata = {}

    return jsons.load({"data": data, "metadata": metadata}, cls=Payload)


def encodes(data: Union[Payload, Iterable[Payload]]) -> str:
    return jsons.dumps(data)
