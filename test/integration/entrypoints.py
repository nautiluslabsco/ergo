import json


def product(payload):
    parsed = json.loads(payload)
    return float(parsed["x"]) * float(parsed["y"])
