from typing import Any, Optional

from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope
from ergo.util import instance_id


class Envelope:
    """
    Use this container to pass data to ergo with custom routing parameters.

    >>> ad_hoc_topic = "interested_party"
    >>> def my_handler(context: Context):
    ...     return context.envelope("my_return_val", topic=f"{context.pubtopic}.{ad_hoc_topic}")
    ...
    >>>
    """

    def __init__(self, data: Any, topic: Optional[str] = None, reply_to: Optional[str] = None):
        self.data = data
        self.topic = topic
        self.reply_to = reply_to


class Context:
    envelope = Envelope

    def __init__(self, message: Message, config: Config):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope

    @property
    def instance_id(self):
        return instance_id()

    def initiate_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        self._scope = self._scope.parent

    def retrieve(self, key: str) -> Any:
        if self._scope:
            return self._scope.data[key]

    def store(self, key: str, value: Any):
        if self._scope:
            self._scope.data[key] = value
