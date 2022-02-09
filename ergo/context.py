from ergo.config import Config
from ergo.message import Message
from ergo.scope import Scope
from ergo.util import instance_id

from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class Envelope:
    data: Any
    reply_to: Optional[str] = None


class Context:
    envelope = Envelope

    def __init__(self, message: Message, config: Config):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope

    @property
    def instance_id(self):
        return instance_id()

    @property
    def scope_id(self) -> str:
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
