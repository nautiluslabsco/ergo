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
        """
        Publish a message with the given topic and data. Receiving components may call `Context.respond` to
        reply directly to the sending instance.

        >>> import random
        >>> x = random.random()
        >>> def requester(context: Context, r=None):
        ...     global x
        ...     if r:
        ...         assert r == x
        ...     else:
        ...         context.request('responder', r=x)
        ...
        >>> def responder(context: Context, r):
        ...     context.respond(r=r)
        ...

        """
        with self._transaction():
            self._stack.set_reply_to(instance_id())
            self._results_stream.send(Payload(data=kwargs or None, key=f"{topic}.request", stack=self._stack))

    def respond(self, data=None, **kwargs):
        """
        See docstring for Context.request.

        """
        if self._stack.get_reply_to() == instance_id():
            # We must be inside a recursive request stack, and the current transaction is associated with a request call
            # that we made in a prior invocation. If its parent is null, then we've reached the 'base case' and should
            # terminate recursion by publishing to our current pubtopic. Otherwise, the parent transaction is associated
            # with the request that we're responding to now.
            self._close_transaction()
        if self._stack:
            key = self._stack.get_reply_to()
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
