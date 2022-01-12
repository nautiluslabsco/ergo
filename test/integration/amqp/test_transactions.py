import json

from test.integration.amqp.utils import AMQP_HOST, publish, subscribe, poll_errors
from test.integration.utils import ergo, Component


def outer_transaction(context):
    context.open_transaction()
    yield {"txn_id": context._transaction_id}


def inner_transaction(context, data):
    parent_txn = data["txn_id"]
    assert parent_txn == context._transaction_id
    context.open_transaction()
    assert parent_txn != context._transaction_id
    assert context._lineage == [parent_txn, context._transaction_id]
    return {"success": True}


def test_transaction(rabbitmq):
    outer_transaction_component = Component(outer_transaction, "outer_transaction_sub", "outer_transaction_pub")
    inner_transaction_component = Component(inner_transaction, "outer_transaction_pub", "inner_transaction_pub")
    inner_transaction_sub = subscribe(inner_transaction_component.pubtopic, inactivity_timeout=0.1)

    with ergo("start", manifest=outer_transaction_component.manifest, namespace=outer_transaction_component.namespace):
        with ergo("start", manifest=inner_transaction_component.manifest, namespace=inner_transaction_component.namespace):
            publish(outer_transaction_component.subtopic, "{}")
            for _, _, body in inner_transaction_sub:
                if body:
                    return
                else:
                    outer_transaction_component.propagate_error(0.1)
                    inner_transaction_component.propagate_error(0.1)
                    # poll_errors([outer_transaction, inner_transaction], inactivity_timeout=0.1)

    
def new_configs(func, subtopic, pubtopic):
    manifest = {
        "func": f"{__file__}:{func.__name__}"
    }
    namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": "test_exchange",
        "pubtopic": pubtopic,
        "subtopic": subtopic,
    }
    return {"manifest": manifest, "namespace": namespace}
