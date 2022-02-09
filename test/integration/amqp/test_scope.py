from typing import Optional, List
from ergo.context import Context
from test.integration.amqp.utils import amqp_component, publish, Queue

"""
test_simple_scope
"""


def simple_scope(context: Context):
    yield 1
    context.initiate_scope()
    yield 2


@amqp_component(simple_scope)
def test_simple_scope(component):
    component.send()
    scopes = [component.consume()["scope"] for _ in range(2)]
    initial_scope, new_scope = sorted(scopes, key=stack_depth)
    assert initial_scope["parent"] is None
    assert new_scope["parent"] == initial_scope


"""
test_downstream_scope
"""


def upstream_scope(context: Context):
    context.initiate_scope()
    yield True
    yield True


def downstream_scope(context: Context):
    context.initiate_scope()
    return True


@amqp_component(downstream_scope, subtopic="upstream_scope_pub")
@amqp_component(upstream_scope, pubtopic="upstream_scope_pub")
def test_downstream_scope(components):
    downstream_component, upstream_component = components
    upstream_component.send()
    upstream_stacks = [upstream_component.consume()["scope"] for _ in range(2)]
    upstream_stacks = sorted(upstream_stacks, key=stack_depth)
    downstream_stacks = [downstream_component.consume()["scope"] for _ in range(2)]
    downstream_stacks = sorted(downstream_stacks, key=stack_depth)

    assert stack_depth(upstream_stacks[0]) == 2
    assert upstream_stacks[0] == upstream_stacks[1]
    assert stack_depth(downstream_stacks[0]) == 3
    assert stack_depth(downstream_stacks[1]) == 3
    assert downstream_stacks[0]["parent"]["id"] == upstream_stacks[0]["id"]
    assert downstream_stacks[1]["parent"]["id"] == upstream_stacks[0]["id"]
    assert downstream_stacks[0]["id"] != downstream_stacks[1]["id"]


"""
test_nested_scope
"""


def nested_scope(context: Context):
    context.initiate_scope()
    yield True
    context.initiate_scope()
    yield True


@amqp_component(nested_scope)
def test_nested_scope(component):
    component.send()
    stacks = [component.consume()["scope"] for _ in range(2)]
    stacks = sorted(stacks, key=stack_depth)
    assert stack_depth(stacks[0]) == 2
    assert stack_depth(stacks[1]) == 3
    assert stacks[1]["parent"] == stacks[0]


"""
test_closing_scope
"""


def closing_scope(context: Context):
    context.initiate_scope()
    yield True
    context.exit_scope()
    yield True


@amqp_component(closing_scope)
def test_closing_scope(component):
    component.send()
    stacks = [component.consume()["scope"] for _ in range(2)]
    stacks = sorted(stacks, key=stack_depth)
    assert stack_depth(stacks[0]) == 1
    assert stack_depth(stacks[1]) == 2


def stack_depth(stack) -> int:
    if stack is None:
        return 0
    return 1 + stack_depth(stack["parent"])


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
