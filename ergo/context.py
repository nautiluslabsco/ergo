from typing import Optional

from ergo.scope import Scope


class Context:
    def __init__(self, pubtopic: str, scope: Optional[Scope]):
        self.pubtopic = pubtopic
        self._scope = scope

    def begin_scope(self):
        self._scope = Scope(parent=self._scope)

    def exit_scope(self):
        if self._scope:
            self._scope = self._scope.parent
