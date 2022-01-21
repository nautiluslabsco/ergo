from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from ergo.util import uniqueid


@dataclass
class Stack:
    id: str = field(default_factory=uniqueid)
    data: Dict = field(default_factory=dict)
    parent: Optional[Stack] = None

    def push(self: Stack) -> Stack:
        return Stack(parent=self)

    def pop(self) -> Optional[Stack]:
        return self.parent

    def get_callback_key(self) -> Optional[str]:
        return self.data.get("callback_key")

    def set_callback_key(self, value: str):
        self.data["callback_key"] = value
