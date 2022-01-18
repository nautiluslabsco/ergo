from test.integration.amqp.utils import AMQPComponent
from typing import Dict


def upstream_transaction(context):
    context._open_transaction()
    yield True
    yield True


def downstream_transaction(context):
    context._open_transaction()
    return True


def test_transaction(rabbitmq):
    with AMQPComponent(downstream_transaction, subtopic="upstream_transaction_pub") as downstream_component:
        with AMQPComponent(upstream_transaction, pubtopic="upstream_transaction_pub") as upstream_component:
            upstream_component.send({})
            upstream_stacks = [upstream_component.consume()["stack"] for _ in range(2)]
            upstream_stacks = sorted(upstream_stacks, key=stack_depth)
            downstream_stacks = [downstream_component.consume()["stack"] for _ in range(2)]
            downstream_stacks = sorted(downstream_stacks, key=stack_depth)

            assert stack_depth(upstream_stacks[0]) == 1
            assert upstream_stacks[0] == upstream_stacks[1]
            assert stack_depth(downstream_stacks[0]) == 2
            assert stack_depth(downstream_stacks[1]) == 2
            assert downstream_stacks[0]["parent"] == upstream_stacks[0]
            assert downstream_stacks[1]["parent"] == upstream_stacks[0]
            assert downstream_stacks[0] != downstream_stacks[1]


def nested_transaction(context):
    context._open_transaction()
    yield
    context._open_transaction()
    yield


def test_nested_transaction(rabbitmq):
    with AMQPComponent(nested_transaction) as component:
        component.send({})
        stacks = [component.consume()["stack"] for _ in range(2)]
        stacks = sorted(stacks, key=stack_depth)
        assert stack_depth(stacks[0]) == 1
        assert stack_depth(stacks[1]) == 2
        assert stacks[1]["parent"] == stacks[0]


def closing_transaction(context):
    context._open_transaction()
    yield
    context._close_transaction()
    yield


def test_closing_transaction(rabbitmq):
    with AMQPComponent(closing_transaction) as component:
        component.send({})
        stacks = [component.consume()["stack"] for _ in range(2)]
        stacks = sorted(stacks, key=stack_depth)
        assert stacks[0] is None
        assert stack_depth(stacks[1]) == 1


def stack_depth(stack) -> int:
    if stack is None:
        return 0
    return 1 + stack_depth(stack["parent"])
