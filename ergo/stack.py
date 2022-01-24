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

    def get_reply_to(self) -> Optional[str]:
        return self.data.get('reply_to')

    def set_reply_to(self, value: str):
        self.data['reply_to'] = value
