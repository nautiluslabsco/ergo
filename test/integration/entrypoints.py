import json


def product(data):
    parsed = json.loads(data)
    return float(parsed["x"]) * float(parsed["y"])


def parse(data):
    parsed = json.loads(data)
    return parsed["return_me"]
