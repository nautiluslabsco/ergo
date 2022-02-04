from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope
from ergo.util import instance_id


class Context:
    def __init__(self, message: Message, config: Config):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope
        self.instance = instance_id()
        self.component = hash(config.func)

    @property
    def scope(self) -> str:
        return self._scope.id

    def subscribe(self, subscriber: str, topic: str):
        if topic == self.scope:
            if subscriber not in self._scope.subscribers:
                self._scope.subscribers.append(subscriber)
        else:
            raise NotImplementedError

    def initiate_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        self._scope = self._scope.parent
