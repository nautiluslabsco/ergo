"""Summary."""
from abc import ABC, abstractmethod
from typing import Iterable, AsyncGenerator

from ergo.invocable import Invocable
from ergo.message import Message


class Invoker(ABC):
    """Summary."""

    def __init__(self, invocable: Invocable) -> None:
        """Summary.

        Args:
            invocable (Invocable): Description

        """
        super().__init__()
        self._invocable = invocable

    @abstractmethod
    def start(self) -> int:
        """Summary.

        Raises:
            NotImplementedError: Description

        """
        raise NotImplementedError()

    async def invoke_handler(self, message_in: Message) -> AsyncGenerator[Message, None]:
        async for message_out in self._invocable.invoke(message_in):
            yield message_out
