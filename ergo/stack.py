from __future__ import annotations
import uuid
from typing import Optional


class Stack:
    def __init__(self, id: Optional[str] = None, parent=None):
        self.id = id or str(uuid.uuid4())
        self.parent: Optional[Stack] = parent

    def push(self: Stack) -> Stack:
        return Stack(parent=self)

    def pop(self) -> Optional[Stack]:
        return self.parent
