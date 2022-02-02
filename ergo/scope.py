from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ergo.util import uniqueid


@dataclass
class Scope:
    id: str = field(default_factory=uniqueid)
    data: dict = field(default_factory=dict)
    parent: Optional[Scope] = None

    @property
    def reply_to(self) -> Optional[str]:
        return self.data.get("reply_to")

    @reply_to.setter
    def reply_to(self, value: str):
        self.data["reply_to"] = value
