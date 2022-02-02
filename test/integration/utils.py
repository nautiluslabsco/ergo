import inspect
import re
import multiprocessing
import tempfile
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager, ContextDecorator
from typing import Callable, Dict, Optional, Type

import yaml

from ergo.ergo_cli import ErgoCli


@contextmanager
def ergo(command, *args, manifest=None, namespace=None):
    """
    This context manager starts a temporary ergo worker in a child process. The worker is terminated at __exit__ time.
    """
    if manifest:
        assert namespace
        with tempfile.NamedTemporaryFile(mode="w+") as manifest_file:
            manifest_file.write(yaml.dump(manifest))
            manifest_file.seek(0)
            with tempfile.NamedTemporaryFile(mode="w+") as namespace_file:
                namespace_file.write(yaml.dump(namespace))
                namespace_file.seek(0)

                with _ergo_inner(command, manifest_file.name, namespace_file.name):
                    yield
    else:
        with _ergo_inner(command, *args):
            yield


@contextmanager
def _ergo_inner(command, *args):
    ergo_process = multiprocessing.Process(
        target=getattr(ErgoCli(), command),
        args=args,
    )
    ergo_process.start()
    try:
        yield
    finally:
        ergo_process.terminate()


class ComponentInstance:
    def __init__(self, manifest: Dict, namespace: Dict):
        self.manifest_file = tempfile.NamedTemporaryFile(mode="w")
        self.manifest_file.write(yaml.dump(manifest))
        self.manifest_file.seek(0)
        self.namespace_file = tempfile.NamedTemporaryFile(mode="w")
        self.namespace_file.write(yaml.dump(namespace))
        self.namespace_file.seek(0)
        self.process = multiprocessing.Process(
            target=ErgoCli().start,
            args=(self.manifest_file.name, self.namespace_file.name),
        )

    def __enter__(self):
        self.process.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manifest_file.close()
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
            except retry_errors:
                if attempt + 1 == n:
                    raise
                time.sleep(backoff_seconds)

        yield retry


class Component(ABC, ContextDecorator):
    def __init__(self, func: Callable):
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
        self._instance: Optional[ComponentInstance] = None

    @property
    @abstractmethod
    def protocol(self):
        return NotImplementedError

    @property
    @abstractmethod
    def host(self):
        return NotImplementedError

    @property
    def manifest(self):
        return {
            "func": f"{self.handler_path}:{self.handler_name}"
        }

    @property
    def namespace(self):
        namespace = {
            "protocol": self.protocol,
            "host": self.host,
        }
        return namespace

    def __enter__(self):
        self._instance = ComponentInstance(self.manifest, self.namespace)
        self._instance.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._instance.__exit__(exc_type, exc_val, exc_tb)

    @contextmanager
    def start(self):
        with ergo("start", manifest=self.manifest, namespace=self.namespace):
            yield
