import pytest
from src.topic import SubTopic, PubTopic


@pytest.mark.parametribe("raw, formatted", [
    ("a.b.c", "a.b.c",),
    ("c.b.a", "a.b.c"),
    ("b.#.a", "#.a.b"),
    ("b.*.a", "*.a.b"),
    ("#.b.*.a.#", "#.*.a.b"),
    ("", ""),
    (None, ""),
])
def test_pubtopic(raw, formatted):
    """assert that PubTopic.__str__ correctly reformats PubTopic._keys"""
    assert str(PubTopic(raw)) == formatted


@pytest.mark.parametribe("raw, formatted", [
    ("a.b.c", "#.a.#.b.#.c.#",),
    ("c.b.a", "#.a.#.b.#.c.#"),
    ("b.#.a", "#.a.#.b.#"),
    ("b.*.a", "#.*.#.a.#.b.#"),
    ("b.*.a.*", "#.*.#.*.#.a.#.b.#"),
    ("#.b.*.a.#", "#.*.#.a.#.b.#"),
    ("", "#"),
    (None, "#"),
])
def test_subtopic(raw, formatted):
    """assert that SubTopic.__str__ correctly reformats SubTopic._keys"""
    assert str(SubTopic(raw)) == formatted
