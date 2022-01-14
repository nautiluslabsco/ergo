import uuid
from typing import List, TypedDict, TypeVar, Optional

import json

from ergo.codec import ErgoSerializable


class Transaction(TypedDict):
    id: str


def new_transaction() -> Transaction:
    return Transaction(id=str(uuid.uuid4()))


TransactionStackType = TypeVar('TransactionStackType', bound='TransactionStack')


class TransactionStack(ErgoSerializable):
    def __init__(self):
        self._stack: List[Transaction] = []

    def push(self):
        self._stack.append(new_transaction())

    def pop(self) -> Transaction:
        return self._stack.pop()

    def top(self) -> Optional[Transaction]:
        if self._stack:
            return self._stack[-1]
        return None

    def extend(self, stack: TransactionStackType):
        self._stack.extend(stack._stack)

    @classmethod
    def from_json(cls, s):
        stack = TransactionStack()
        stack._stack = json.loads(s)
        return stack

    def to_json(self):
        return self._stack

    def __len__(self):
        return len(self._stack)

    def __iter__(self):
        return self._stack.__iter__()

    def __str__(self):
        return str(self._stack)
