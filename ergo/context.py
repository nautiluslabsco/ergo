from typing import Optional

from ergo.stack import Stack


class Context:
    def __init__(self, pubtopic: str, stack: Optional[Stack]):
        self.pubtopic = pubtopic
        self.stack = stack

    def open_transaction(self):
        if self.stack:
            self.stack = self.stack.push()
        else:
            self.stack = Stack()

    def close_transaction(self):
        if self.stack:
            self.stack = self.stack.pop()
