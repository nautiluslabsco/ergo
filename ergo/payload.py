"""Summary."""
import copy
import json
from typing import Any, Dict, List, Optional, TypedDict
from ergo.transaction import TransactionStack
import pydash


DATA_KEY = "data"
METADATA_KEY = "metadata"


class _PrivateMetadata(TypedDict, total=False):
    key: str
    log: List
    transaction_stack: TransactionStack
    error: str
    traceback: str


class Metadata(_PrivateMetadata, total=False):
    pubtopic: str


class ErgoMessage(Metadata):
    metadata: Metadata
    data: Any


_PrivateMetadataKeys = set(_PrivateMetadata.__annotations__.keys())


class Payload:
    """Summary."""

    def __init__(self, message: ErgoMessage) -> None:
        """Summary.

        Args:
            data (Optional[Dict[str, str]], optional): Description

        """
        self.contents = message

    @classmethod
    def assemble(cls, data=None, metadata: Dict=None, **kwargs):
        # TODO after all messages written with the old schema have been consumed
        # data = data or kwargs
        # metadata = metadata or {}
        # return cls(ErgoMessage(data=data, metadata=metadata))

        if data:
            # assume message is normalized
            # metadata in its own key means message message was written with the new schema
            # metadata in unpacked kwargs means message was written with the old deprecated schema
            metadata = metadata or kwargs
        else:
            # assume message is un-normalized (not sent by ergo)
            data = kwargs
            metadata = metadata or {}
        return cls(ErgoMessage(data=data, metadata=metadata))

    @property
    def meta(self) -> Metadata:
        return self.contents["metadata"]

    def get(self, key: str, default=None):
        """Summary.

        Args:
            key (str): Description

        Returns:
            Optional[str]: Description

        """
        value = pydash.get(self.contents["data"], key)
        if value:
            return value
        if key not in _PrivateMetadataKeys:
            return pydash.get(self.contents, key, default)
        return default

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description

        """
        return json.dumps(self.contents)
