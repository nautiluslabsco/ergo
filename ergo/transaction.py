import uuid
from typing import List, TypedDict, Optional, TypeVar

import ergo.container


class TransactionData(TypedDict):
    id: str


class Transaction(ergo.container.Container[TransactionData]):
    pass


def new_transaction() -> Transaction:
    return Transaction(TransactionData(id=str(uuid.uuid4())))


TransactionStackData = List[Transaction]


_TransactionStack = TypeVar('_TransactionStack', bound='TransactionStack')


class TransactionStack(ergo.container.Container[TransactionStackData]):
    def push(self, txn: Transaction):
        self._contents.append(txn)

    def pop(self) -> Transaction:
        return self._contents.pop()

    def top(self) -> Optional[Transaction]:
        if self._contents:
            return self._contents[-1]
        return None

    def extend(self, stack: _TransactionStack):
        self._contents.extend(stack._contents)

    def __len__(self):
        return len(self._contents)

    def __iter__(self):
        return self._contents.__iter__()


def new_transaction_stack():
    return TransactionStack([])
