"""Summary."""
from abc import ABC, abstractmethod
from typing import Generator

from ergo.context import Context
from ergo.function_invocable import FunctionInvocable
from ergo.payload import Payload


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
        context = Context(pubtopic=self._invocable.config.pubtopic.raw(), stack=payload_in.stack)
        for data_out in self._invocable.invoke(context, payload_in):
            payload_out = Payload(data=data_out, stack=context._stack, key=context.pubtopic)
            yield payload_out
