"""Summary."""
from abc import ABC, abstractmethod
from typing import Generator

from ergo.function_invocable import FunctionInvocable
from ergo.payload import Payload
from ergo.util import instance_id


class Invoker(ABC):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        """Summary.

        Args:
            invocable (FunctionInvocable): Description

        """
        super().__init__()
        self.instance_id = instance_id()
        self._invocable = invocable

    @abstractmethod
    def start(self) -> int:
        """Summary.

        Raises:
            NotImplementedError: Description

        """
        raise NotImplementedError()

    def invoke_handler(self, payload_in: Payload) -> Generator[Payload, None, None]:
        yield from self._invocable.invoke(payload_in)
