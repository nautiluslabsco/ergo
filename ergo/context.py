from ergo.config import Config
from ergo.message import Message
from ergo.receiver import Receiver
from ergo.scope import Scope
from ergo.util import instance_id

from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class Envelope:
    data: Any
    reply_to: Optional[str] = None
    initiate_request: bool = False

    def is_request(self):
        return bool(self.reply_to or self.initiate_request)


class Context:
    envelope = Envelope

    def __init__(self, message: Message, config: Config, component_receiver: Receiver, instance_receiver: Receiver):
        self.pubtopic: str = config.pubtopic
        self._scope = message.scope
        self.component = component_receiver
        self.instance = instance_receiver

    @property
    def instance_id(self):
        return instance_id()

    @property
    def scope_id(self) -> str:
        return self._scope.id

    # def envelope(self, data: Any, reply_to: Optional[str] = None, initiate_request: bool = False):
    #     e = Envelope(data=data, reply_to=reply_to, initiate_request=initiate_request)
    #     if e.is_request():
    #         self.initiate_scope()
    #     self._scope.metadata["reply_to"] = reply_to
    #     return e

    def initiate_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        self._scope = self._scope.parent
