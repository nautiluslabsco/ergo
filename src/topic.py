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
        self._raw: str = topic_str or ""

    def extend(self, topic_str: str):
        """
        extend returns a new Topic object with additional keys given in `topic_str`

        >>> topic = PubTopic("a.b")
        >>> str(topic)
        'a.b'
        >>> extended = topic.extend("c")
        >>> str(topic)
        'a.b'
        >>> str(extended)
        'a.b.c'

        """
        if self._raw:
            topic_str = ".".join([self._raw, topic_str])
        return type(self)(topic_str)

    def _keys(self):
        return [Key(key_str) for key_str in self._raw.split('.')]

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description
        """
        ret = '#'
        if self._keys:
            ret = '#.%s.#' % '.#.'.join(sorted([str(key) for key in self._keys()]))
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
        ret = '.'.join(sorted([str(key) for key in self._keys()]))
        return ret
