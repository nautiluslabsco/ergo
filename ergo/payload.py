"""Summary."""
import json
from typing import Any, Dict, List, Optional

import pydash


class Payload:
    """Summary."""

    def __init__(self, key: Optional[str], log: List, data: Any) -> None:
        """Summary.

        Args:
            data (Optional[Dict[str, str]], optional): Description

        """
        self._data: Dict = {"key": key, "log": log, "data": data}

    @classmethod
    def from_string(cls, data: str):
        return cls.from_dict(json.loads(data))

    @classmethod
    def from_dict(cls, data: Dict):
        key = data.get("key")
        log = data.pop("log", [])
        payload = cls(key=key, log=log, data=data)
        return payload

    @property
    def log(self) -> List:
        return self._data["log"]

    def get(self, key: str, default=None):
        """Summary.

        Args:
            key (str): Description

        Returns:
            Optional[str]: Description

        """
        return pydash.get(self._data, key) or default

    def set(self, key: str, value: str) -> None:
        """Summary.

        Args:
            key (str): Description
            value (str): Description

        """
        self._data[key] = value

    def unset(self, key: str):
        """Summary.

        Args:
            key (str): Description

        """
        return self._data.pop(key, None)

    def list(self) -> List[str]:
        """Summary.

        Returns:
            List[str]: Description

        """
        return list(self._data.values())

    def __str__(self) -> str:
        """Summary.

        Returns:
            str: Description

        """
        return json.dumps(self._data)
