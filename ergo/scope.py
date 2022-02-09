from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TypedDict

from ergo.util import uniqueid


@dataclass
class Scope:
    id: str = field(default_factory=uniqueid)
    metadata: dict = field(default_factory=dict)
    parent: Optional[Scope] = None

    @property
    def reply_to(self):
        return self.metadata.get("reply_to")

    @reply_to.setter
    def reply_to(self, value: str):
        self.metadata["reply_to"] = value
