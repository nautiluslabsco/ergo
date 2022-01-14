import uuid
from typing import List, Optional, TypeVar


class Transaction:
    def __init__(self):
        self.id: str = str(uuid.uuid4())

    def __str__(self):
        return self.id


TransactionStackType = TypeVar('TransactionStackType', bound='TransactionStack')


class TransactionStack:
    def __init__(self):
        self._stack: List[Transaction] = []

    def push(self):
        self._stack.append(Transaction())

    def pop(self) -> Transaction:
        return self._stack.pop()

    def top(self) -> Optional[Transaction]:
        if self._stack:
            return self._stack[-1]
        return None

    def extend(self, stack: TransactionStackType):
        self._stack.extend(stack._stack)

    def __str__(self):
        return self._stack.__str__()
