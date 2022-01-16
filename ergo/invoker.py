"""Summary."""
from abc import ABC, abstractmethod
from typing import Generator

from ergo.context import Context
from ergo.function_invocable import FunctionInvocable
from ergo.payload import Metadata, Payload
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
        new_stack = Stack()
        ctx = Context(pubtopic=self._invocable.config.pubtopic.raw(), stack=new_stack)
        for data_out in self._invocable.invoke(ctx, payload_in):
            parent_stack = payload_in.metadata.stack
            if new_stack:
                parent_stack.extend(new_stack)
            meta_out = Metadata(stack=parent_stack, key=ctx.pubtopic)
            meta_out.stack = parent_stack
            payload_out = Payload(data=data_out, metadata=meta_out)
            yield payload_out
