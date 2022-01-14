import json
from abc import ABC, abstractmethod


class ErgoSerializable(ABC):
    @classmethod
    @abstractmethod
    def from_json(cls, s):
        raise NotImplementedError

    def to_json(self) -> str:
        raise NotImplementedError
