"""Summary."""
import json
from typing import Any, Dict, List, Optional, Type


class Payload:
    """Summary."""

    def __init__(self, data: Optional[Dict[str, Any]] = None, encoder=None) -> None:
        """Summary.

        Args:
            data (Optional[Dict[str, Any]], optional): Description
            encoder (Optional[Type[json.JSONEncoder]], optional): Description

        """
        self._data: Dict[str, Any] = data or {}
        self._encoder: Optional[Type[json.JSONEncoder]] = encoder

    def get(self, key: str) -> Optional[str]:
        """Summary.

        Args:
            key (str): Description

        Returns:
            Optional[str]: Description

        """
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        """Summary.

        Args:
            key (str): Description
            value (Any): Description

        """
        self._data[key] = value

    def list(self) -> List[Any]:
        """Summary.

        Returns:
            List[Any]: Description

        """
        return list(self._data.values())

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: JSON string representation of data

        """
        return json.dumps(self._data, cls=self._encoder)
