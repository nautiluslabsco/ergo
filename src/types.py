"""Summary.

Attributes:
    TYPE_PAYLOAD (TYPE): Return value from bound function
    TYPE_RETURN (TYPE): Standardized payload object

"""
from typing import Any, Dict
from src.payload import Payload

TYPE_PAYLOAD = Dict[str, Any]
TYPE_RETURN = Payload
