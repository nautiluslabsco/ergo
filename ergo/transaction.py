import uuid
from typing import List, TypedDict


class Transaction(TypedDict):
    id: str


def new_transaction() -> Transaction:
    return Transaction(id=str(uuid.uuid4()))


TransactionStack = List[Transaction]


def new_transaction_stack() -> TransactionStack:
    return []
