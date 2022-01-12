"""Summary."""
import copy
import json
from typing import Any, Dict, List, Optional, TypedDict
from ergo.transaction import TransactionStack
from ergo.context import Context
import pydash
from contextlib import contextmanager


# @dataclasses.dataclass
# class Metadata:
#     key: Optional[str] = None
#     log: Optional[List] = dataclasses.field(default_factory=list)
#     transaction_stack: Optional[TransactionStack] = dataclasses.field(default_factory=TransactionStack)
#     error: Optional[str] = None
#     traceback: Optional[str] = None

# Metadata = TypedDict("Metadata", total=False, fields={
#     "key": str,
#     "log": List,
#     "transaction_stack": TransactionStack,
#     "error": str,
#     "traceback": str
# })

DATA_PARAM = "data"


class _TransparentMetadata(TypedDict, total=False):
    pubtopic: str


class Metadata(_TransparentMetadata, total=False):
    key: str
    log: List
    transaction_stack: TransactionStack
    error: str
    traceback: str


class Payload:
    """Summary."""
    @classmethod
    def new(cls, data: Any, metadata: Metadata):
        try:
            return cls(metadata=metadata, **data)
        except TypeError:
            return cls(metadata=metadata, DATA_PARAM=data)

    def __init__(self, metadata: Optional[Metadata] = None, **data) -> None:
        """Summary.

        Args:
            data (Optional[Dict[str, str]], optional): Description

        """
        self._data: Dict = data
        self.metadata: Metadata = metadata or Metadata()


    # @classmethod
    # def from_string(cls, data: str):
    #     return cls.from_dict(json.loads(data))
    #
    # @classmethod
    # def from_dict(cls, data: Dict):
    #     meta = data.pop("metadata")
    #     payload = cls(key=key, log=log, transaction_stack=transaction_stack, data=data)
    #     return payload


    @property
    def meta(self) -> Dict:
        return self.metadata

    def get(self, key: str, default=None):
        """Summary.

        Args:
            key (str): Description

        Returns:
            Optional[str]: Description

        """

        if key in _TransparentMetadata.__annotations__:
            if key in self.metadata:
                return self.metadata[key]
        value = pydash.get(self._data, key)
        if value:
            return value
        if key == DATA_PARAM:
            return self._data
        return default

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description

        """
        return json.dumps({"metadata": self.meta, **self._data})
