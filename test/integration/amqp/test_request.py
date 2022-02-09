from test.integration.amqp.utils import Queue, amqp_component, publish
from typing import List, Optional

from ergo.context import Context


def fizzbuzz_generator(context: Context):
    for x in range(1, 16):
        yield context.envelope({"x": x}, initiate_request=True)


def fizzes(x: int):
    return {x: "Fizz" if x % 3 == 0 else x}


def buzzes(x: int):
    return {x: "Buzz" if x % 5 == 0 else x}


def fizzbuzz_accumulator(context: Context, data):
    return data
    # assert False


@amqp_component(fizzbuzz_generator, subtopic="fizzbuzz.start", pubtopic="fizzbuzz.compute")
@amqp_component(fizzes, subtopic="fizzbuzz.compute", pubtopic="fizzbuzz.accumulator")
@amqp_component(buzzes, subtopic="fizzbuzz.compute", pubtopic="fizzbuzz.accumulator")
@amqp_component(fizzbuzz_accumulator, subtopic="fizzbuzz.accumulator")
def test_fizzbuzz(components):
    publish("fizzbuzz.start")
    # while True:
    #     pass
    accumulator_component = components[-1]
    while True:
        data = accumulator_component.consume()["data"]
        assert data
        print(data)
    assert False


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
                context.pubtopic = child
                yield context.envelope({}, reply_to=context.instance_id)
        else:
            yield {"path": self.id}


node_a = Node('a', children=['b'])
node_b = Node('b', children=['c', 'd'])
node_c = Node('c')
node_d = Node('d')


@amqp_component(node_a, subtopic='tree.traverse', pubtopic='tree.path')
@amqp_component(node_b, subtopic='b.request')
@amqp_component(node_c, subtopic='c.request')
@amqp_component(node_d, subtopic='d.request')
def test_traverse_tree(components):
    queue = Queue("tree.path")
    publish("tree.traverse")
    results = [queue.consume()['data']['path'] for _ in range(2)]
    results = sorted(results)
    assert results == ['a.b.c', 'a.b.d']


"""
test_request

        a
       / \
      b   d
    /
   c

"""


def a(context: Context):
    return context.envelope(True, initiate_request=True)


def b():
    return True


def c():
    return True


def d(context: Context):
    context.initiate_scope()
    return True


@amqp_component(a, pubtopic="a")
@amqp_component(b, subtopic="a", pubtopic="b")
@amqp_component(c, subtopic="b", pubtopic="c")
@amqp_component(d, subtopic="a", pubtopic="d")
def test_request(components):
    component_a, component_b, component_c, component_d = components
    component_a.send()
    result_b = component_b.consume()
    assert "response" in result_b["key"].split(".")
    result_c = component_c.consume()
    assert "response" not in result_c["key"].split(".")
    result_d = component_d.consume()
    assert "response" not in result_d["key"].split(".")
    for result in [result_b, result_c, result_d]:
        assert "request" not in result["key"].split(".")
