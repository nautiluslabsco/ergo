from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from ergo.util import uniqueid


@dataclass
class Scope:
    id: str = field(default_factory=uniqueid)
    metadata: dict = field(default_factory=dict)
    parent: Optional[Scope] = None

    @property
    def subscribers(self) -> List:
        if "subscribers" not in self.metadata:
            self.metadata["subscribers"] = []
        return self.metadata["subscribers"]
