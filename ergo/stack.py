from __future__ import annotations

from typing import Optional
from dataclasses import dataclass, field
from ergo.util import uniqueid


@dataclass
class Stack:
    id: str = field(default_factory=uniqueid)
    parent: Optional[Stack] = None

    def push(self: Stack) -> Stack:
        return Stack(parent=self)

    def pop(self) -> Optional[Stack]:
        return self.parent
