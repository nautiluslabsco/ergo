"""Summary."""
import json
from typing import Any, Dict, List, Optional, TypedDict
from ergo.transaction import TransactionStack
import dataclasses
import pydash


DATA_KEY = "data"


@dataclasses.dataclass
class Metadata:
    key: Optional[str] = None
    log: List = dataclasses.field(default_factory=list)
    transaction_stack: TransactionStack = dataclasses.field(default_factory=TransactionStack)
    error: Optional[Dict[str, str]] = None
    traceback: Optional[str] = None


_MetadataFields = set(Metadata.__annotations__)


@dataclasses.dataclass()
class ErgoMessage:
    metadata: Metadata
    data: Any


class Payload:
    def __init__(self, message: ErgoMessage):
        self._message = message

    @property
    def meta(self) -> Metadata:
        return self._message.metadata


class InboundPayload(Payload):
    def __init__(self, data=None, metadata: Dict=None, **kwargs):
        # TODO after all messages written with the old schema have been consumed
        # data = data or kwargs
        # metadata = metadata or {}
        # return cls(context, ErgoMessage(data=data, metadata=metadata))

        if data:
            # assume _message is normalized
            # metadata in its own key means _message _message was written with the new schema
            # metadata in unpacked kwargs means _message was written with the old deprecated schema
            raw_metadata = metadata or kwargs
        else:
            # assume _message is un-normalized (not sent by ergo)
            data = kwargs
            raw_metadata = metadata or {}

        filtered_metadata = {key: value for key, value in (raw_metadata or {}).items() if key in _MetadataFields}
        processed_metadata = Metadata(**filtered_metadata)
        ergo_message = ErgoMessage(data=data, metadata=processed_metadata)
        super().__init__(ergo_message)

    def get(self, key: str, default=None):
        """Summary.

        Args:
            key (str): Description

        Returns:
            Optional[str]: Description

        """
        value = pydash.get(self._message.data, key)
        if value:
            return value
        if key == DATA_KEY:
            return self._message.data
        return default


class OutboundPayload(Payload):
    def __init__(self, message: ErgoMessage) -> None:
        super().__init__(message)

    def __str__(self):
        return json.dumps(self._message, cls=PayloadEncoder)


class PayloadEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ErgoMessage) or isinstance(o, Metadata):
            return o.__dict__
        if isinstance(o, TransactionStack):
            return str(o)
        return super().default(o)
