import uuid
from typing import Optional, TypeVar

TYPE_STACK = TypeVar('TYPE_STACK', bound='Stack')


class Stack:
    def __init__(self, id: Optional[str] = None, parent=None):
        self.id = id or str(uuid.uuid4())
        self.parent: Optional[TYPE_STACK] = parent

    def push(self) -> TYPE_STACK:
        return Stack(parent=self)

    def pop(self) -> TYPE_STACK:
        return self.parent
