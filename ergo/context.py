from ergo.transaction import Stack, Transaction


class Context:
    def __init__(self, pubtopic: str, stack: Stack):
        self.pubtopic = pubtopic
        self._stack = stack

    def open_transaction(self):
        self._stack.push(Transaction())

    def close_transaction(self):
        self._stack.pop()
