import uuid
from dataclasses import dataclass, field
from typing import List, Optional, TypeVar


@dataclass
class Transaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


_Stack = TypeVar('_Stack', bound='Stack')


class Stack:
    def __init__(self, transactions: Optional[List[Transaction]] = None):
        self._transactions = transactions or []

    def push(self, transaction: Transaction):
        self._transactions.append(transaction)

    def pop(self) -> Transaction:
        return self._transactions.pop()

    def top(self) -> Optional[Transaction]:
        if self._transactions:
            return self._transactions[-1]
        return None

    def extend(self, stack: _Stack):
        self._transactions.extend(stack._transactions)

    def __len__(self):
        return len(self._transactions)

    def __iter__(self):
        return self._transactions.__iter__()
