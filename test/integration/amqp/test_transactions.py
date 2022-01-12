import json

from test.integration.amqp.utils import amqp_component


def outer_transaction(context):
    assert context._transaction is None
    context.open_transaction()
    yield {"txn_id": context._transaction}


def inner_transaction(context, data):
    parent_txn = data["txn_id"]
    assert parent_txn == context._transaction
    context.open_transaction()
    assert parent_txn != context._transaction
    context.close_transaction()
    assert parent_txn == context._transaction
    return {"success": True}


def test_transaction(rabbitmq):
    with amqp_component(outer_transaction, subtopic="outer_transaction_sub", pubtopic="outer_transaction_pub") as outer_transaction_component:
        with amqp_component(inner_transaction, subtopic="outer_transaction_pub", pubtopic="inner_transaction_pub") as inner_transaction_component:
            sub = inner_transaction_component.subscribe(inactivity_timeout=0.1)
            outer_transaction_component.publish()
            for attempt in range(20):
                outer_transaction_component.propagate_error(0.1)
                inner_transaction_component.propagate_error(0.1)
                result = next(sub)
                if result:
                    assert result["data"] == "success"
