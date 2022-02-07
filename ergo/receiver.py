from abc import ABC, abstractmethod


class Receiver(ABC):
    @abstractmethod
    def subscribe(self, topic: str):
        pass
