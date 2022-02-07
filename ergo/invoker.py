"""Summary."""
from abc import ABC, abstractmethod
from typing import Generator

from ergo.function_invocable import FunctionInvocable
from ergo.message import Message
from ergo.receiver import Receiver


class Invoker(ABC):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        """Summary.

        Args:
            invocable (FunctionInvocable): Description

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

    def invoke_handler(self, message_in: Message, component_receiver: Receiver, instance_receiver: Receiver) -> Generator[Message, None, None]:
        yield from self._invocable.invoke(message_in, component_receiver, instance_receiver)
