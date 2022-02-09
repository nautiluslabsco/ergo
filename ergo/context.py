from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope
from ergo.util import instance_id

from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class Envelope:
    data: Any
    pubtopic: Optional[str] = None
    reply_to: Optional[str] = None


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
