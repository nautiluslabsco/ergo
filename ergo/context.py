from typing import Optional

from ergo.stack import Scope


class Context:
    def __init__(self, pubtopic: str, scope: Optional[Scope]):
        self.pubtopic = pubtopic
        self._scope = scope

    def _open_scope(self):
        self._scope = Scope(parent=self._scope)

    def _close_scope(self):
        if self._scope:
            self._scope = self._scope.parent
