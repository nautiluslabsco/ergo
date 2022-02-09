from test.integration.amqp.utils import Queue, amqp_component, publish
from typing import List, Optional

from ergo.context import Context

"""
test_fibonacci

"""


def fibonacci_trigger(context: Context):
    return context.envelope({}, reply_to="fibonacci.filter")


def fibonacci_generator(i=0, j=1):
    if i < 100:
        return {"i": j, "j": i+j}


def fibonacci_filter(i):
    return i


@amqp_component(fibonacci_trigger, subtopic="fibonacci.start", pubtopic="fibonacci.generator")
@amqp_component(fibonacci_generator, subtopic="fibonacci.generator", pubtopic="fibonacci.generator")
@amqp_component(fibonacci_filter, subtopic="fibonacci.filter", pubtopic="fibonacci.next")
def test_fibonacci(components):
    results_queue = Queue("fibonacci.next")
    publish("fibonacci.start")
    results = [results_queue.consume()["data"] for _ in range(10)]
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
                context.pubtopic = child
                yield context.envelope({}, reply_to=context.instance_id)
        else:
            yield {"path": self.id}


node_a = Node('a', children=['b'])
node_b = Node('b', children=['c', 'd'])
node_c = Node('c')
node_d = Node('d')


@amqp_component(node_a, subtopic='tree.traverse', pubtopic='tree.path')
@amqp_component(node_b, subtopic='b')
@amqp_component(node_c, subtopic='c')
@amqp_component(node_d, subtopic='d')
def test_traverse_tree(components):
    queue = Queue("tree.path")
    publish("tree.traverse")
    results = [queue.consume()['data']['path'] for _ in range(2)]
    results = sorted(results)
    assert results == ['a.b.c', 'a.b.d']
