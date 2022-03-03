import inspect
import multiprocessing
import re
import tempfile
import time
from contextlib import ContextDecorator, contextmanager
from typing import Callable, Dict, Optional, Type, List
from abc import ABC, abstractmethod

import yaml

from ergo.ergo_cli import ErgoCli


class ComponentInstance:
    def __init__(self, ergo_command: str, *configs: Dict):
        self.config_files = []
        for config in configs:
            config_file = tempfile.NamedTemporaryFile(mode="w")
            config_file.write(yaml.dump(config))
            config_file.seek(0)
            self.config_files.append(config_file)
        args = tuple(cf.name for cf in self.config_files)
        self.process = multiprocessing.Process(target=getattr(ErgoCli(), ergo_command), args=args)

    def __enter__(self):
        self.process.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for config_file in self.config_files:
            config_file.close()
        self.process.terminate()


def retries(n: int, backoff_seconds: float, *retry_errors: Type[Exception]):
    success: set = set()
    for attempt in range(n):
        if success:
            break

        @contextmanager
        def retry():
            try:
                yield
                success.add(True)
            except retry_errors or Exception:
                if attempt + 1 == n:
                    raise
                time.sleep(backoff_seconds)

        yield retry


class Component(ContextDecorator, ABC):
    _ergo_command = "start"

    def __init__(self):
        self._instance: Optional[ComponentInstance] = None

    @property
    @abstractmethod
    def namespace(self) -> dict:
        raise NotImplementedError

    @property
    def configs(self) -> List[dict]:
        return [self.namespace]

    def __enter__(self):
        self._instance = ComponentInstance(self._ergo_command, *self.configs)
        self._instance.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._instance.__exit__(exc_type, exc_val, exc_tb)


class FunctionComponent(Component, ABC):
    def __init__(self, func: Callable):
        super().__init__()
        self.func = func
        if inspect.isfunction(func):
            self.handler_path = inspect.getfile(func)
            self.handler_name = func.__name__
        else:
            # func is an instance method, and we have to get hacky to find the module variable it was assigned to
            frame = inspect.currentframe()
            frame = inspect.getouterframes(frame)[2]
            string = inspect.getframeinfo(frame[0]).code_context[0].strip()
            self.handler_path = inspect.getfile(func.__call__)
            self.handler_name = re.search(r"\((.*?)[,)]", string).group(1)

    @property
    def manifest(self):
        return {
            "func": f"{self.handler_path}:{self.handler_name}"
        }

    @property
    def configs(self) -> List[dict]:
        return [self.manifest, self.namespace]
