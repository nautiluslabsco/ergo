from src.function_invocable import FunctionInvocable


class HttpInvoker:
    def __init__(self, invocable: FunctionInvocable) -> None:
        super().__init__()
        self._invocable = invocable
        self._route: str = '/'
        self._port: int = 80

    @property
    def route(self) -> str:
        return self._route

    @route.setter
    def route(self, arg: str) -> None:
        self._route = arg

    @property
    def port(self) -> int:
        return self._port

    @port.setter
    def port(self, arg: int) -> None:
        self._port = arg
