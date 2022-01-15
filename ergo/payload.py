"""Summary."""
import json
from typing import Any, Dict, List, Optional, TypedDict
from ergo.transaction import TransactionStack, Transaction
from ergo.codec import ErgoSerializable
import pydash


DATA_KEY = "data"


class Metadata(TypedDict, total=False):
    key: str
    log: List
    transaction_stack: TransactionStack
    error: Dict[str, str]
    traceback: str


def new_metadata() -> Metadata:
    return Metadata(log=[], transaction_stack=TransactionStack())


def decode_metadata(raw_metadata) -> Metadata:
    transaction_stack = TransactionStack(raw_metadata.pop("transaction_stack", None))
    return Metadata(transaction_stack=transaction_stack, **raw_metadata)


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
    def __init__(self, data=None, metadata: Optional[Dict] = None, **kwargs):
        # TODO after all messages written with the old schema have been consumed
        # data = data or raw_metadata
        # metadata = metadata or {}
        # return cls(context, ErgoMessage(data=data, metadata=metadata))

        if data:
            # assume _message is normalized
            # metadata in its own key means _message _message was written with the new schema
            # metadata in unpacked raw_metadata means _message was written with the old deprecated schema
            meta: Metadata = decode_metadata(metadata or kwargs)
        else:
            # assume _message is un-normalized (not sent by ergo)
            data = kwargs
            meta = new_metadata()

        super().__init__(ErgoMessage(data=data, metadata=meta))

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

    def __str__(self):
        return json.dumps(self._message, cls=PayloadEncoder)


class PayloadEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ErgoSerializable):
            return o.to_json()
        return super().default(o)
