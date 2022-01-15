from typing import Generic, TypeVar
import json


T = TypeVar('T')


class Container(Generic[T]):
    def __init__(self, contents: T):
        self._contents: T = contents

    def json(self):
        return self._contents

    def __repr__(self):
        return json.dumps(self, cls=ErgoEncoder)


class ErgoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Container):
            return o.json()
        return super().default(o)
