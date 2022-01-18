from __future__ import annotations

from typing import Optional

from ergo.util import uniqueid


class Stack:
    def __init__(self, id: Optional[str] = None, parent=None):
        self.id = id or uniqueid()
        self.parent: Optional[Stack] = parent

    def push(self: Stack) -> Stack:
        return Stack(parent=self)

    def pop(self) -> Optional[Stack]:
        return self.parent
