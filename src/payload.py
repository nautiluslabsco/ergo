from typing import Dict, List, Optional


class Payload:
    def __init__(self, data: Optional[Dict[str, str]] = None) -> None:
        self._data: Dict[str, str] = data or {}

    def get(self, key: str) -> Optional[str]:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def list(self) -> List[str]:
        return list(self._data.values())

    def __str__(self):
      return str(self._data)