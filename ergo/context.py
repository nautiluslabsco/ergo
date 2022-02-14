from typing import Any

from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope


class Context:
    def __init__(self, message: Message, config: Config):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope

    def initiate_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        if self._scope:
            self._scope = self._scope.parent

    def retrieve(self, key: str) -> Any:
        if self._scope:
            return self._scope.data[key]

    def store(self, key: str, new_data: Any):
        if self._scope:
            self._scope.data[key] = new_data
