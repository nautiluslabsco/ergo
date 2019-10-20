import importlib.util
import os
import re
import sys
from importlib.abc import Loader
from typing import Callable, Optional

from src.payload import Payload
from src.types import TYPE_RETURN


class FunctionInvocable:
    def __init__(self, reference: str) -> None:
        self._func: Optional[Callable[..., TYPE_RETURN]] = None  # type: ignore
        self._reference: str = reference
        self.inject()

    @property
    def func(self) -> Optional[Callable[..., TYPE_RETURN]]:  # type: ignore
        return self._func

    @func.setter
    def func(self, arg: Callable[..., TYPE_RETURN]) -> None:  # type: ignore
        self._func = arg

    def invoke(self, data_out: Payload, data_in: Payload) -> None:
        result: TYPE_RETURN = None
        if not self._func:
            raise Exception('Cannot executeNo injected function')
        try:
            result = self._func(*data_in.list())
        except Exception as err:
            raise Exception(f'Referenced function {self._reference} threw an exception: {str(err)}')

        data_out.set('result', result)

    def inject(self) -> None:
        # [path/to/file/[file.extension[:[class.]method]]]
        pattern = r'^(.*\/)?([^\.\/]+)\.([^\.]+):([^:]+\.)?([^:\.]+)$'  # (path/to/file/)(file).(extension):(method)
        matches = re.match(pattern, self._reference)
        if not matches:
            raise Exception(f'Unable to inject invalid referenced function {self._reference}')

        path_to_source_file = matches.group(1)
        if not matches.group(1):
            path_to_source_file = os.getcwd()
        elif matches.group(1)[0] != '/':
            path_to_source_file = f'{os.getcwd()}/{matches.group(1)}'
        source_file_name = matches.group(2)
        source_file_extension = matches.group(3)
        sys.path.insert(0, path_to_source_file)

        spec = importlib.util.spec_from_file_location(source_file_name, f'{path_to_source_file}/{source_file_name}.{source_file_extension}')
        module = importlib.util.module_from_spec(spec)
        assert isinstance(spec.loader, Loader)  # see https://github.com/python/typeshed/issues/2793
        spec.loader.exec_module(module)

        scope = module
        if matches.group(4):
            class_name = matches.group(4)[:-1]
            scope = getattr(scope, class_name)

        method_name = matches.group(5)
        self._func = getattr(scope, method_name)
