import inspect
import multiprocessing
import re
import tempfile
import time
from abc import ABC, abstractmethod
from contextlib import ContextDecorator, contextmanager
from typing import Callable, Dict, Optional, Type

import yaml

from ergo.ergo_cli import ErgoCli


class ComponentInstance:
    def __init__(self, ergo_command: str, manifest: Optional[Dict] = None, namespace: Optional[Dict] = None):
        self.manifest_file = self.namespace_file = None
        args = []
        if manifest:
            self.manifest_file = tempfile.NamedTemporaryFile(mode="w")
            self.manifest_file.write(yaml.dump(manifest))
            self.manifest_file.seek(0)
            args.append(self.manifest_file.name)
        if namespace:
            self.namespace_file = tempfile.NamedTemporaryFile(mode="w")
            self.namespace_file.write(yaml.dump(namespace))
            self.namespace_file.seek(0)
            args.append(self.namespace_file.name)
        self.process = multiprocessing.Process(target=getattr(ErgoCli(), ergo_command), args=tuple(args))

    def __enter__(self):
        self.process.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.manifest_file:
            self.manifest_file.close()
        if self.namespace_file:
            self.namespace_file.close()
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


class Component(ABC, ContextDecorator):
    _ergo_command = "start"

    def __init__(self):
        self._instance: Optional[ComponentInstance] = None

    @property
    def namespace(self):
        return None

    @property
    def manifest(self):
        return None

    def __enter__(self):
        self._instance = ComponentInstance(self._ergo_command, manifest=self.manifest, namespace=self.namespace)
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
            self.handler_name = re.search("\((.*?)[,)]", string).group(1)

    @property
    def manifest(self):
        return {
            "func": f"{self.handler_path}:{self.handler_name}"
        }

