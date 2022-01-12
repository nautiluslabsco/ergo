import inspect
import json
import time
import multiprocessing
import yaml
import tempfile
from typing import Type, Callable, Optional
from contextlib import contextmanager
from ergo.ergo_cli import ErgoCli
from abc import ABC, abstractmethod


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
                if attempt+1 == n:
                    raise
                time.sleep(backoff_seconds)

        yield retry


class Component(ABC):
    def __init__(self, func: Callable):
        self.func = func
        self.queue = f"{inspect.getfile(func)}:{func.__name__}"
        self.error_queue = f"{self.queue}_error"

    @property
    @classmethod
    @abstractmethod
    def protocol(cls):
        return NotImplementedError

    @property
    @classmethod
    @abstractmethod
    def host(cls):
        return NotImplementedError

    @property
    def manifest(self):
        return {
            "func": f"{inspect.getfile(self.func)}:{self.func.__name__}"
        }

    @property
    def namespace(self):
        namespace = {
            "protocol": self.protocol,
            "host": self.host,
            "exchange": "test_exchange",
        }
        return namespace

    @contextmanager
    def start(self):
        with ergo("start", manifest=self.manifest, namespace=self.namespace):
            yield
