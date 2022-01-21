from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from ergo.payload import Payload
from ergo.results_stream import ResultsStream
from ergo.stack import Stack
from ergo.util import instance_id


class Context:
    def __init__(self, pubtopic: str, stack: Optional[Stack], results_stream: ResultsStream):
        self.pubtopic = pubtopic
        self._stack = stack
        self._results_stream = results_stream

    def request(self, topic: str, **kwargs):
        with self._transaction():
            self._stack.set_callback_key(instance_id())
            self._results_stream.send(Payload(data=kwargs or None, key=f"{topic}.request", stack=self._stack))

    def respond(self, data=None, **kwargs):
        if self._stack.get_callback_key() == instance_id():
            self._close_transaction()
        if self._stack:
            key = self._stack.get_callback_key()
        else:
            key = self.pubtopic
        self._results_stream.send(Payload(data=data or kwargs, key=key, stack=self._stack))

    @contextmanager
    def _transaction(self):
        self._open_transaction()
        try:
            yield
        finally:
            self._close_transaction()

    def _open_transaction(self):
        if self._stack:
            self._stack = self._stack.push()
        else:
            self._stack = Stack()

    def _close_transaction(self):
        if self._stack:
            self._stack = self._stack.pop()
