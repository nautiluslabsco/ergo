import json
from typing import Any

from src.config import Config
from src.payload import Payload
from src.topic import Topic


def serialize(data: Any) -> str:
    return json.dumps(data, cls=ErgoEncoder)


class ErgoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Config):
            return o.__dict__
        elif isinstance(o, Topic):
            return str(o)
        elif isinstance(o, Payload):
            return o._data
        return json.JSONEncoder.default(self, o)
