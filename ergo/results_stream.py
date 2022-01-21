from collections.abc import Generator
from typing import List

from ergo.payload import Payload


class ResultsStream(Generator):
    def __init__(self):
        self.results: List[Payload] = []

    def __next__(self) -> Payload:
        try:
            return self.results.pop(0)
        except IndexError:
            raise StopIteration

    def send(self, payload: Payload):
        self.results.append(payload)

    def throw(self, *args, **kwargs):
        raise StopIteration
