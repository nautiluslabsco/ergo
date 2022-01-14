from ergo.transaction import TransactionStack


class Context:
    def __init__(self, pubtopic: str):
        self.pubtopic = pubtopic
        self._transaction_stack = TransactionStack()

    def open_transaction(self):
        self._transaction_stack.push()

    def close_transaction(self):
        self._transaction_stack.pop()
