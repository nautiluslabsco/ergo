from typing import Optional, Union
from contextlib import contextmanager
from ergo.transaction import Transaction
from ergo.topic import PubTopic


class Context:
    def __init__(self):
        self._transaction: Optional[Transaction] = None
        self._pubtopic: Optional[PubTopic] = None

    def open_transaction(self):
        if not self._transaction:
            self._transaction = Transaction()

    @property
    def pubtopic(self) -> Optional[PubTopic]:
        return self._pubtopic

    @pubtopic.setter
    def pubtopic(self, value: Union[str, PubTopic]):
        if isinstance(value, str):
            value = PubTopic(value)
        self._pubtopic = value

    # @contextmanager
    # def set_pubtopic(self, pubtopic: str):
    #     try:
    #         self._pubtopic = pubtopic
    #         yield
    #     finally:
    #         self._pubtopic = None
