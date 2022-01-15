from ergo.transaction import TransactionStack, new_transaction


class Context:
    def __init__(self, pubtopic: str, transaction_stack: TransactionStack):
        self.pubtopic = pubtopic
        self._transaction_stack = transaction_stack

    def open_transaction(self):
        self._transaction_stack.push(new_transaction())

    def close_transaction(self):
        self._transaction_stack.pop()
