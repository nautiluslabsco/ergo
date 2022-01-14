"""Summary."""
import json
from typing import Any, Dict, List, Optional, TypedDict
from ergo.transaction import TransactionStack, Transaction, new_transaction_stack
import dataclasses
import pydash


DATA_KEY = "data"


class Metadata(TypedDict, total=False):
    key: str
    log: List
    transaction_stack: TransactionStack
    error: Dict[str, str]
    traceback: str


def new_metadata() -> Metadata:
    return Metadata(log=[], transaction_stack=new_transaction_stack())


class ErgoMessage(TypedDict):
    metadata: Metadata
    data: Any


class Payload:
    def __init__(self, message: ErgoMessage):
        self._message = message

    @property
    def meta(self) -> Metadata:
        return self._message["metadata"]


class InboundPayload(Payload):
    def __init__(self, data=None, metadata: Optional[Metadata] = None, **kwargs):
        # TODO after all messages written with the old schema have been consumed
        # data = data or kwargs
        # metadata = metadata or {}
        # return cls(context, ErgoMessage(data=data, metadata=metadata))

        if data:
            # assume _message is normalized
            # metadata in its own key means _message _message was written with the new schema
            # metadata in unpacked kwargs means _message was written with the old deprecated schema
            metadata = metadata or kwargs
        else:
            # assume _message is un-normalized (not sent by ergo)
            data = kwargs
            metadata = new_metadata()

        super().__init__(ErgoMessage(data=data, metadata=metadata))

    def get(self, key: str, default=None):
        """Summary.

        Args:
            key (str): Description

        Returns:
            Optional[str]: Description

        """
        value = pydash.get(self._message["data"], key)
        if value:
            return value
        if key == DATA_KEY:
            return self._message["data"]
        return default


class OutboundPayload(Payload):
    def __init__(self, message: ErgoMessage) -> None:
        super().__init__(message)

    def serialize(self) -> str:
        return json.dumps(self._message)
