"""Summary."""
from typing import Any, Dict, List, Optional, TypedDict
from ergo.transaction import TransactionStack, TransactionStackData, new_transaction_stack
from ergo.container import Container
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


def decode_metadata(raw_metadata) -> Metadata:
    transaction_stack = TransactionStack(raw_metadata.pop("transaction_stack", new_transaction_stack()))
    return Metadata(transaction_stack=transaction_stack, **raw_metadata)


class PayloadContents(TypedDict):
    metadata: Metadata
    data: Any


class Payload(Container[PayloadContents]):
    @property
    def meta(self) -> Metadata:
        return self._contents["metadata"]

    def get(self, key: str, default=None):
        """Summary.

        Args:
            key (str): Description

        Returns:
            Optional[str]: Description

        """
        value = pydash.get(self._contents["data"], key)
        if value:
            return value
        if key == DATA_KEY:
            return self._contents["data"]
        return default


def decode_message(data=None, metadata: Optional[Dict] = None, **kwargs) -> Payload:
    # TODO after all messages written with the old schema have been consumed
    # data = data or raw_metadata
    # metadata = metadata or {}
    # return cls(context, PayloadContents(data=data, metadata=metadata))

    if data:
        # assume _contents is normalized
        # metadata in its own key means _contents _contents was written with the new schema
        # metadata in unpacked raw_metadata means _contents was written with the old deprecated schema
        meta: Metadata = decode_metadata(metadata or kwargs)
    else:
        # assume _contents is un-normalized (not sent by ergo)
        data = kwargs
        meta = new_metadata()

    return Payload(PayloadContents(data=data, metadata=meta))
