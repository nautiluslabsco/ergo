"""Summary."""
from typing import List, Optional

from src.key import Key


class Topic:
    """Summary."""

    def __init__(self, topic_str: Optional[str]):
        """Summary.

        Args:
            topic_str (str): Description
        """
        self._keys: List[Key] = []
        if topic_str:
            self._keys = [Key(key_str) for key_str in topic_str.split('.')]

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description
        """
        ret = '#'
        if self._keys:
            ret = '#.%s.#' % '.#.'.join(sorted([str(key) for key in self._keys]))
        return ret


class SubTopic(Topic):
    """Summary."""


class PubTopic(Topic):
    """Summary."""

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description
        """
        ret = '.'.join(sorted([str(key) for key in self._keys]))
        return ret
