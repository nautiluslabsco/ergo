from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from ergo.util import uniqueid


@dataclass
class Scope:
    id: str = field(default_factory=uniqueid)
    data: dict = field(default_factory=dict)
    parent: Optional[Scope] = None

    @property
    def cc(self) -> List:
        if 'cc' not in self.data:
            self.data['cc'] = []
        return self.data['cc']
