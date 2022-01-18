from typing import Optional

from ergo.stack import Stack


class Context:
    def __init__(self, pubtopic: str, stack: Optional[Stack]):
        self.pubtopic = pubtopic
        self._stack = stack

    def _open_transaction(self):
        if self._stack:
            self._stack = self._stack.push()
        else:
            self._stack = Stack()

    def _close_transaction(self):
        if self._stack:
            self._stack = self._stack.pop()
