"""Summary."""
from abc import ABC, abstractmethod
from typing import Generator

from ergo.context import Context
from ergo.function_invocable import FunctionInvocable
from ergo.payload import Payload
from ergo.transaction import Stack


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

    def invoke_handler(self, payload_in: Payload) -> Generator[Payload, None, None]:
        parent_stack = payload_in.stack
        context = Context(pubtopic=self._invocable.config.pubtopic.raw(), stack=parent_stack)
        for data_out in self._invocable.invoke(context, payload_in):
            payload_out = Payload(data=data_out, stack=parent_stack, key=context.pubtopic)
            yield payload_out
