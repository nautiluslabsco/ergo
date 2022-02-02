from collections.abc import Generator
from typing import List

from ergo.message import Message


class ResultsStream(Generator):
    def __init__(self):
        self.results: List[Message] = []

    def __next__(self) -> Message:
        try:
            return self.results.pop(0)
        except IndexError:
            raise StopIteration

    def send(self, message: Message):
        self.results.append(message)

    def throw(self, *args, **kwargs):
        raise StopIteration
