from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope


class Context:
    def __init__(self, message: Message, config: Config):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope

    def begin_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        if self._scope:
            self._scope = self._scope.parent
