"""Summary."""
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


class Metadata(TypedDict, total=False):
    key: str
    log: List
    transaction_stack: TransactionStack
    error: str
    traceback: str


class Payload:
    """Summary."""

    def __init__(self, metadata: Optional[Metadata] = None, **data) -> None:
        """Summary.

        Args:
            data (Optional[Dict[str, str]], optional): Description

        """
        self._data: Dict = data
        self.metadata: Metadata = metadata or Metadata()
        self.context = Context()


    # @classmethod
    # def from_string(cls, data: str):
    #     return cls.from_dict(json.loads(data))
    #
    # @classmethod
    # def from_dict(cls, data: Dict):
    #     key = data.pop("key", None)
    #     log = data.pop("log", [])
    #     transaction_stack = data.pop("transaction_stack", [])
    #     payload = cls(key=key, log=log, transaction_stack=transaction_stack, data=data)
    #     return payload
    #
    # def get(self, key: str, default=None):
    #     """Summary.
    #
    #     Args:
    #         key (str): Description
    #
    #     Returns:
    #         Optional[str]: Description
    #
    #     """
    #     if key == "context":
    #         return self.context
    #     return pydash.get(self._data, key, default)

    @property
    def meta(self) -> Dict:
        return self.metadata

    @contextmanager
    def share(self, *args: str, **kwargs: str) -> Dict:
        # values = {key: self.data.get(key) for key in args}
        # values.update({key: self.data.get(key, default) for key, default in kwargs.items()})
        kwargs.update({arg: None for arg in args})
        values = {}
        for key, default in kwargs.items():
            if key == "context":
                values[key] = self.context
            else:
                values[key] = pydash.get(self._data, key, default)
        yield values

    def set(self, key: str, value: str) -> None:
        """Summary.

        Args:
            key (str): Description
            value (str): Description

        """
        self._data[key] = value

    def unset(self, key: str):
        """Summary.

        Args:
            key (str): Description

        """
        return self._data.pop(key, None)

    def list(self) -> List[str]:
        """Summary.

        Returns:
            List[str]: Description

        """
        return list(self._data.values())

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description

        """
        return json.dumps({
            "metadata": self.meta,
            "data": self._data,
        })
