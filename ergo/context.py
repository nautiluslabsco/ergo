from ergo.topic import PubTopic
from typing import Optional, TypedDict, List
import uuid
from contextlib import contextmanager


Transaction = uuid.UUID
TransactionLineage = List[Transaction]


class Context:
    def __init__(self, lineage: Optional[TransactionLineage] = None):
        self._lineage: TransactionLineage = lineage or []
        self._owns_current_transaction: bool = False
        self._pubtopic: Optional[str] = None

    def open_transaction(self):
        if not self._owns_current_transaction:
            self._owns_current_transaction = True
            self._lineage.append(uuid.uuid4())

    @contextmanager
    def set_pubtopic(self, pubtopic: str):
        try:
            self._pubtopic = pubtopic
            yield
        finally:
            self._pubtopic = None
