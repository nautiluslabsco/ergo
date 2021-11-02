from src import topic


def test_extend_subtopic():
    original = topic.SubTopic("x.y")
    assert str(original) == "#.x.#.y.#"
    extended = original.extend("b.a")
    assert str(original) == "#.x.#.y.#"
    assert str(extended) == "#.a.#.b.#.x.#.y.#"


def test_extend_pubtopic():
    original = topic.PubTopic(None)
    assert str(original) == ""
    extended = original.extend("b.a")
    assert str(original) == ""
    assert str(extended) == "a.b"
