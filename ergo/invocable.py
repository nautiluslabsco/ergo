from abc import ABC, abstractmethod
from typing import AsyncGenerator

from ergo.message import Message
from ergo.config import Config


class Invocable(ABC):
    def __init__(self, config: Config):
        self._config: Config = config

    @property
    def config(self) -> Config:
        """Summary.

        Returns:
            Config: Description

        """
        return self._config

    @abstractmethod
    async def invoke(self, message_in: Message) -> AsyncGenerator[Message, None]:
        pass
