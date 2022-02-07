"""Summary."""
import signal
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator

from ergo.function_invocable import FunctionInvocable
from ergo.message import Message


class Invoker(ABC):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        """Summary.

        Args:
            invocable (FunctionInvocable): Description

        """
        super().__init__()
        self._invocable = invocable
        self._signum = None
        self._terminating = False

    @abstractmethod
    def start(self) -> int:
        """Summary.

        Raises:
            NotImplementedError: Description

        """
        raise NotImplementedError()

    def invoke_handler(self, message_in: Message) -> Generator[Message, None, None]:
        yield from self._invocable.invoke(message_in)

    @contextmanager
    def defer_termination(self):
        """
        Use this context manager to temporarily postpone SIGTERM handling.
        """
        prev_handler = signal.signal(signal.SIGTERM, self._sigterm_handler)
        try:
            yield
        finally:
            signal.signal(signal.SIGTERM, prev_handler)
            if self._signum:
                signal.raise_signal(signal.SIGTERM)

    def _sigterm_handler(self, signum, _):
        self._signum = signum
        self._terminating = True
