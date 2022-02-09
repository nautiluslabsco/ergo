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
