import pytest

from test.integration.utils.amqp import amqp_component, Queue, publish, SHORT_TIMEOUT
from typing import List, Optional

from ergo.context import Context

"""
test_shout
"""


def shout(context: Context, message=None, capitalized=None):
    if capitalized:
        return f"{capitalized}!"

    return context.envelope(message, topic="capitalize", reply_to=context.instance_id)


def capitalize(data: str):
    return {"capitalized": data.upper()}


@amqp_component(shout)
@amqp_component(capitalize, subtopic="capitalize")
def test_shout(components):
    shout_component = components[0]
    result = shout_component.rpc(message="hey")["data"]
    assert result == "HEY!"


"""
test_reply_to_scope

Each node in the tree below is implemented with a component. Orchestrator publishes a message with reply_to="my_results"
in scope. That scope is propagated through the whole tree, but node d initiates a new scope before publishing. Thus
a, b, and c should reply to topic "my_results", while d should not.

    orchestrator
        |
        a
       / \
      b   d
    /
   c
"""


def orchestrator(context: Context):
    return context.envelope(None, topic="a", reply_to="my_results")


def a(context: Context):
    return context.envelope("a", topic="b.d")


def b(context: Context):
    return context.envelope("b", topic="c")


def c():
    return "c"


def d(context: Context):
    context.initiate_scope()
    return "d"


def test_reply_to_scope():
    results_queue = Queue("my_results")
    c_orchestrator = amqp_component(orchestrator, subtopic="test_reply_to_scope")
    c_a = amqp_component(a, subtopic="a")
    c_b = amqp_component(b, subtopic="b")
    c_c = amqp_component(c, subtopic="c")
    c_d = amqp_component(d, subtopic="d")
    with results_queue, c_orchestrator, c_a, c_b, c_c, c_d:
        # publish({}, "test_reply_to_scope")
        c_orchestrator.send()
        results = sorted([results_queue.get().data for _ in range(3)])
        assert results == ["a", "b", "c"]
        assert c_d.consume()["data"] == "d"
        with pytest.raises(Exception):
            results_queue.get(timeout=SHORT_TIMEOUT)


"""
test_fibonacci

The fibonacci_iterator component below publishes to its own subtopic in order to generate an infinite fibonacci 
sequence. Because this loop operates in a continuous scope containing reply_to="filter", the fibonacci_filter
component should receive each message it publishes.
"""


def fibonacci_orchestrator(context: Context):
    return context.envelope(None, reply_to="filter")


def fibonacci_iterator(i=0, j=1):
    if j < 100:
        return {"i": j, "j": i + j}


def fibonacci_filter(i=None):
    return i


def test_fibonacci():
    orchestrator_component = amqp_component(fibonacci_orchestrator, subtopic="start", pubtopic="iterate")
    iterator_component = amqp_component(fibonacci_iterator, subtopic="iterate", pubtopic="iterate")
    filter_component = amqp_component(fibonacci_filter, subtopic="filter", pubtopic="next")
    results_queue = Queue("next")
    with orchestrator_component, iterator_component, filter_component, results_queue:
        publish({}, "start")
        results = [results_queue.get().data for _ in range(10)]
        assert results == [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]


"""
test_traverse_tree
Each node in the tree below is implemented with a component. The test sends a message to node A,
which recursively requests a path from each of its children, and then responds with that path, prepended with its 
own name. Node A should ultimately publish two strings, 'a.b.c' and 'a.b.d'.

        a
        |
        b
      /   \
    c       d
"""


class Node:
    def __init__(self, name: str, children: Optional[List[str]] = None):
        self.id = name
        self.children: List[str] = children or []

    def __call__(self, context: Context, path=None):
        if path:
            yield {"path": f'{self.id}.{path}'}
        elif self.children:
            for child in self.children:
                yield context.envelope(None, topic=child, reply_to=context.instance_id)
        else:
            yield {"path": self.id}


node_a = Node('a', children=['b'])
node_b = Node('b', children=['c', 'd'])
node_c = Node('c')
node_d = Node('d')


def test_traverse_tree():
    queue = Queue("tree.path")
    with (
        amqp_component(node_a, subtopic='tree.traverse', pubtopic='tree.path'),
        amqp_component(node_b, subtopic='b'),
        amqp_component(node_c, subtopic='c'),
        amqp_component(node_d, subtopic='d'),
        queue,
    ):
        publish({}, "tree.traverse")
        results = [queue.get().data['path'] for _ in range(2)]
        results = sorted(results)
        assert results == ['a.b.c', 'a.b.d']


# @pytest.fixture(scope="session", autouse=True)
# def teardown_module():
#     yield
#     import time
#     while True:
#         print("sleeping")
#         time.sleep(1000)
