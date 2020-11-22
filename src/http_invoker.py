# unfortunately pylint is not able to recognize abstract subclasses
# pylint: disable=W0223

"""Summary."""
from src.function_invocable import FunctionInvocable
from src.invoker import Invoker


class HttpInvoker(Invoker):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        """Summary.

        Args:
            invocable (FunctionInvocable): Description

        """
        super().__init__(invocable)
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
