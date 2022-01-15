import json
from abc import ABC, abstractmethod


class ErgoSerializable(ABC):
    @classmethod
    @abstractmethod
    def from_json(cls, s):
        raise NotImplementedError

    def to_json(self) -> str:
        raise NotImplementedError


class ErgoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ErgoSerializable):
            return o.to_json()
        return super().default(o)


class ErgoDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, object_pairs_hook=self.object_pairs_hook, *args, **kwargs)

    def object_hook(self, data):
        return data

    def object_pairs_hook(self, *args, **kwargs):
        return args


def deserialize(s: str):
    return json.loads(s, cls=ErgoDecoder)
