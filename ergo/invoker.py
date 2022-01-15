"""Summary."""
from abc import ABC, abstractmethod

from ergo.function_invocable import FunctionInvocable
from ergo.payload import Payload, Metadata
from ergo.context import Context
from typing import Generator


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
        ctx = Context(pubtopic=self._invocable.config.pubtopic.raw())
        for data_out in self._invocable.invoke(ctx, payload_in):
            stack = payload_in.meta["transaction_stack"]
            stack.extend(ctx._transaction_stack)
            meta = Metadata(transaction_stack=stack, key=ctx.pubtopic)
            payload_out = Payload({"data": data_out, "metadata": meta})
            yield payload_out
