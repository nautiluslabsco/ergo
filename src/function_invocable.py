"""Summary."""
import inspect
from typing import Callable, Generator, Optional

from src.config import Config
from src.types import TYPE_PAYLOAD, TYPE_RETURN
from src.util import load_source, log, print_exc_plus


class FunctionInvocable:
    """Summary."""

    def __init__(self, config: Config) -> None:
        """Summary.

        Args:
            reference (str): Description

        """
        self._func: Optional[Callable[..., TYPE_RETURN]] = None  # type: ignore
        self._config: Config = config
        self.inject()

    @property
    def config(self) -> Config:
        """Summary.

        Returns:
            Config: Description

        """
        return self._config

    @property
    def func(self) -> Optional[Callable[..., TYPE_RETURN]]:  # type: ignore
        """Summary.

        Returns:
            Optional[Callable[..., TYPE_RETURN]]: Bound function

        """
        return self._func

    @func.setter
    def func(self, arg: Callable[..., TYPE_RETURN]) -> None:  # type: ignore
        """Summary.

        Args:
            arg (Callable[..., TYPE_RETURN]): Description

        """
        self._func = arg

    def invoke(self, data_in: TYPE_RETURN) -> Generator[TYPE_PAYLOAD, None, None]:
        """Invoke injected function.

        If func is a generator, will exhaust generator, yielding each response.
        If an exception occurs will re-raise with a stack trace.
        Func responses will not be percolated if they return None.

        Args:
            data_in (TYPE_RETURN): dict with a 'data' key. Corresponding value will be passed to injected function.

        Raises:
            Exception:
                * caught exception re-raised with a stack trace.
                * function was not specified in configuration and cannot be invoked

        """
        if not self._func:
            raise Exception('Cannot execute injected function')
        try:
            if inspect.isgeneratorfunction(self._func):
                result_exp = self._func(data_in['data'])
            else:
                result_exp = (r for r in [self._func(data_in['data'])])

            for result in result_exp:
                yield TYPE_PAYLOAD(data={'data': result, 'log': log(data_in.get('log', []))}, encoder=self._encoder)

        except BaseException as err:
            raise Exception(print_exc_plus()) from err

    def inject(self) -> None:
        """Summary.

        Raises:
            Exception: failure to inject function due to non-existing or invalid reference

        """
        try:
            self._func = load_source(self._config.func)
            self._encoder = load_source(self._config.encoder)
        except Exception as err:
            raise Exception(f'Unable to inject invalid referenced function {self._config.func}') from err

