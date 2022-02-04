from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope
from ergo.util import instance_id


class Context:
    def __init__(self, message: Message, config: Config):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope

    def subscribe_to_scope(self):
        self.add_scope_subscriber(instance_id())

    def add_scope_subscriber(self, topic: str):
        assert self._scope
        if topic not in self._scope.subscribers:
            self._scope.subscribers.append(topic)

    def initiate_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        if self._scope:
            self._scope = self._scope.parent
