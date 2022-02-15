"""Summary."""


class Key:
    """Summary."""

    def __init__(self, key_str: str):
        """Summary.

        Args:
            key_str (str): Description
        """
        self._key = key_str

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description
        """
        return self._key

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return self.__str__().__hash__()
