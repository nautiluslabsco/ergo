from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope
from ergo.util import instance_id


class Context:
    def __init__(self, message: Message, config: Config):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope

    @property
    def instance_id(self):
        return instance_id()

    def add_scope_cc(self, topic: str):
        assert self._scope
        if topic not in self._scope.cc:
            self._scope.cc.append(topic)

    def initiate_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        if self._scope:
            self._scope = self._scope.parent
