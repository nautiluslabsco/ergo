from test.integration.amqp.utils import amqp_component


def outer_transaction(context):
    assert context._transaction is None
    context.open_transaction()
    assert context._transaction is not None


def inner_transaction(context):
    assert context._transaction is None
    context.open_transaction()
    assert context._transaction is not None
    return {"success": True}


def test_transaction(rabbitmq):
    with amqp_component(outer_transaction, subtopic="outer_transaction_sub", pubtopic="outer_transaction_pub") as outer_transaction_component:
        with amqp_component(inner_transaction, subtopic="outer_transaction_pub", pubtopic="inner_transaction_pub") as inner_transaction_component:
            outer_sub = outer_transaction_component.new_subscription(inactivity_timeout=5)
            inner_sub = inner_transaction_component.new_subscription(inactivity_timeout=5)
            outer_transaction_component.publish()
            outer_txn_stack = next(outer_sub)["metadata"]["transaction_stack"]
            assert len(outer_txn_stack) == 1
            inner_txn_stack = next(inner_sub)["metadata"]["transaction_stack"]
            assert len(inner_txn_stack) == 2
            assert inner_txn_stack[0] == outer_txn_stack[0]
