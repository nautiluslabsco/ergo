from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ergo.util import uniqueid


@dataclass
class Scope:
    id: str = field(default_factory=uniqueid)
    metadata: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)
    parent: Optional[Scope] = None

    @property
    def reply_to(self) -> Optional[str]:
        return self.metadata.get("reply_to")

    @reply_to.setter
    def reply_to(self, value: str):
        self.metadata["reply_to"] = value

    @property
    def correlation_id(self) -> Optional[str]:
        return self.metadata.get("correlation_id")

    @correlation_id.setter
    def correlation_id(self, value: str):
        self.metadata["correlation_id"] = value
