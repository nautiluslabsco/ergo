"""Summary."""
from abc import ABC, abstractmethod

from src.function_invocable import FunctionInvocable


class HttpInvoker(ABC):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        """Summary.

        Args:
            invocable (FunctionInvocable): Description

        """
        super().__init__()
        self._invocable = invocable
        self._route: str = '/'
        self._port: int = 80

    @property
    def route(self) -> str:
        """Summary.

        Returns:
            str: Description

        """
        return self._route

    @route.setter
    def route(self, arg: str) -> None:
        """Summary.

        Args:
            arg (str): Description

        """
        self._route = arg

    @property
    def port(self) -> int:
        """Summary.

        Returns:
            int: Description

        """
        return self._port

    @port.setter
    def port(self, arg: int) -> None:
        """Summary.

        Args:
            arg (int): Description

        """
        self._port = arg

    @abstractmethod
    def start(self) -> int:
        """Summary.

        Raises:
            NotImplementedError: Description

        """
        raise NotImplementedError()
