from abc import ABC, abstractmethod


class Serializable(ABC):
    @classmethod
    @abstractmethod
    def deserialize(cls, s):
        raise NotImplementedError

    def serialize(self) -> str:
        raise NotImplementedError
