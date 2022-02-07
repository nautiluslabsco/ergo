from ergo.config import Config
from ergo.message import Message
from ergo.receiver import Receiver
from ergo.scope import Scope


class Context:
    def __init__(self, message: Message, config: Config, component_receiver: Receiver, instance_receiver: Receiver):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope
        self.component = component_receiver
        self.instance = instance_receiver

    @property
    def scope(self) -> str:
        return self._scope.id

    def initiate_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        self._scope = self._scope.parent
