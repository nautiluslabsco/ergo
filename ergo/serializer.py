import json
from abc import ABC


class JSONEncodable(ABC):
    def json(self):
        raise NotImplementedError


def serialize(obj) -> str:
    return json.dumps(obj, cls=ErgoEncoder)


class ErgoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, JSONEncodable):
            return o.json()
        return super().default(o)
