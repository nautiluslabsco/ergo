from __future__ import annotations

from contextlib import contextmanager

from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope
from ergo.results_stream import ResultsStream
from ergo.util import instance_id


class Context:
    def __init__(self, message: Message, config: Config, results_stream: ResultsStream):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope
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
        with self.new_scope():
            self._scope.reply_to = f"{instance_id()}_{topic.replace('.', '_')}"
            self._results_stream.send(Message(data=kwargs or None, key=topic, scope=self._scope))

    @contextmanager
    def new_scope(self):
        self.begin_scope()
        try:
            yield
        finally:
            self.exit_scope()

    def begin_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        if self._scope:
            self._scope = self._scope.parent
