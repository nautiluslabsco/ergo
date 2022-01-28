from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, TypeVar, Generic, Dict

from ergo.util import uniqueid


T = TypeVar('T')


class Stack(Generic[T]):
    def __init__(self, elements: Optional[List[T]]):
        self._elements: List[T] = elements or []

    def push(self, element: T):
        return self._elements.append(element)

    def pop(self) -> Optional[Stack]:
        return self.parent


class Scope:
    def __init__(self, id: Optional[str] = None, parent: Optional[Scope] = None):
        self.id = id or uniqueid()
        self.parent = parent

    def _stack(self) -> List[Dict]:
        stack = [{'id': self.id}]
        if self.parent:
            stack.extend(self.parent._stack())
        return stack

    def __repr__(self):
        return str(self._stack())
