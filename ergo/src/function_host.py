import importlib.util
import os
import re
from importlib.abc import Loader
from typing import Any


class FunctionHost:
    def __init__(self, reference: str) -> None:
        self._func: Any = None
        self._reference: str = reference
        self.inject()

    @property
    def func(self) -> Any:
        return self._func

    @func.setter
    def func(self, arg: Any) -> None:
        self._func = arg

    def invoke(self, data_in: Any, data_out: Any) -> None:
        result: Any = None

        try:
            result = self._func(*data_in)
        except Exception as err:
            raise Exception(f'Referenced function {self._reference} threw an exception: {str(err)}')

        data_out.append(result)

    def inject(self,) -> None:
        pattern = r'^([^\.]+)\.([^\.]+):([^:]+)$'
        matches = re.match(pattern, self._reference)
        if not matches:
            raise Exception(f'Unable to inject invalid referenced function {self._reference}')
        meta = [f'{os.getcwd()}/{matches.group(1)}.{matches.group(2)}', matches.group(1), matches.group(3)]
        spec = importlib.util.spec_from_file_location(meta[1], meta[0])
        module = importlib.util.module_from_spec(spec)
        assert isinstance(spec.loader, Loader)  # see https://github.com/python/typeshed/issues/2793
        spec.loader.exec_module(module)
        self._func = getattr(module, meta[2])
