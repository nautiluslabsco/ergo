"""Summary."""
import json
from typing import Any, Dict, List, Optional, TypedDict
from ergo.transaction import TransactionStack
from ergo.context import Context
import pydash


class _PrivateMetadata(TypedDict, total=False):
    key: str
    log: List
    transaction_stack: TransactionStack
    error: Dict[str, str]
    traceback: str


class Metadata(_PrivateMetadata, total=False):
    pubtopic: str


class ErgoMessage(Metadata):
    metadata: Metadata
    data: Any


_PrivateMetadataKeys = set(_PrivateMetadata.__annotations__.keys())


class Payload:
    def __init__(self, message: ErgoMessage):
        self._message = message

    @property
    def meta(self) -> Metadata:
        return self._message["metadata"]


class InboundPayload(Payload):
    def __init__(self, context: Context, data=None, metadata: Dict=None, **kwargs):
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
            metadata = metadata or {}

        super().__init__(ErgoMessage(data=data, metadata=metadata))
        self.context = context

    def get(self, key: str, default=None):
        """Summary.

        Args:
            key (str): Description

        Returns:
            Optional[str]: Description

        """
        if key == "context":
            return self.context
        value = pydash.get(self._message["data"], key)
        if value:
            return value
        if key not in _PrivateMetadataKeys:
            return pydash.get(self._message, key, default)
        return default


class OutboundPayload(Payload):
    def __init__(self, message: ErgoMessage) -> None:
        super().__init__(message)

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description

        """
        return json.dumps(self._message)
