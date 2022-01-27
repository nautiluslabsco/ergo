from typing import Optional, List
from ergo.context import Context
from test.integration.amqp.utils import amqp_component

"""
test_ping_pong
"""


def ping(context: Context, response=None):
    if response:
        return {'ping': response}
    context.request('pong', ping=True)


def pong(context: Context, data):
    if data.get('ping'):
        context.respond(response='pong')


@amqp_component(ping, subtopic="ping_sub", pubtopic="ping_pub")
@amqp_component(pong, subtopic='pong', pubtopic="pong_pub")
def test_ping_pong(components):
    ping_component = components[0]
    ping_component.send()
    while True:
        bh = True
    result = ping_component.rpc()['data']
    assert result == {'ping': 'pong'}


"""
test_traverse_tree

Each node in the tree below is implemented with a component. The test sends a message to node A,
which recursively requests a path from each of its children, and then responds with that path, prepended with its 
own ID. Node A should ultimately publish two strings, 'a.b.c' and 'a.b.d'.

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
            context.respond(path=f'{self.id}.{path}')
        elif self.children:
            for child in self.children:
                context.request(f'traverse.{child}')
        else:
            context.respond(path=self.id)


node_a = Node('a', children=['b'])
node_b = Node('b', children=['c', 'd'])
node_c = Node('c')
node_d = Node('d')


@amqp_component(node_a, subtopic='a')
@amqp_component(node_b, subtopic='b')
@amqp_component(node_c, subtopic='c')
@amqp_component(node_d, subtopic='d')
def test_traverse_tree(components):
    root_node = components[0]
    root_node.send()
    while True:
        bh = True
    results = [root_node.consume()['data']['path'] for _ in range(2)]
    results = sorted(results)
    assert results == ['a.b.c', 'a.b.d']
