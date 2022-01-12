import uuid
from typing import List


class Transaction(str):
    def __new__(cls):
        return str(uuid.uuid4())


TransactionStack = List[Transaction]
