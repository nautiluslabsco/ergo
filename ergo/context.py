from ergo.transaction import new_transaction_stack, new_transaction


class Context:
    def __init__(self, pubtopic: str):
        self.pubtopic = pubtopic
        self._transaction_stack = new_transaction_stack()

    def open_transaction(self):
        self._transaction_stack.append(new_transaction())

    def close_transaction(self):
        self._transaction_stack.pop()
