from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ergo.util import uniqueid


@dataclass
class Scope:
    id: str = field(default_factory=uniqueid)
    data: dict = field(default_factory=dict)
    parent: Optional[Scope] = None

    def store(self, key: str, value):
        self.data[key] = value

    def retrieve(self, key):
        return self.data.get(key)
