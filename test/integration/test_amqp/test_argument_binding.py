from test.integration.utils.amqp import Queue, amqp_component, publish_pika

from ergo.context import Context

"""
These tests assert that ergo can correctly bind message data to a custom parameter using the `args` configuration attribute.
"""


def handler_with_mapped_params(my_context: Context, my_param):
    assert isinstance(my_context, Context)
    return my_param


@amqp_component(handler_with_mapped_params, args={"my_param": "data", "my_context": "context"})
def test_bind_data_to_my_param(component):
    """
    Component configuration contains

    args:
      - my_context: context
      - my_param: data

    ergo should bind the full payload to `my_param`
    """
    results = Queue(routing_key=component.pubtopic)
    publish_pika(component.subtopic, foo="bar")
    assert results.consume()["data"] == {"foo": "bar"}
    publish_pika(component.subtopic, data={"foo": "bar"})
    assert results.consume()["data"] == {"foo": "bar"}
    publish_pika(component.subtopic, data="foo")
    assert results.consume()["data"] == "foo"
    publish_pika(component.subtopic, something_else="bar")
    assert results.consume()["data"] == {"something_else": "bar"}


@amqp_component(handler_with_mapped_params, args={"my_param": "data.foo", "my_context": "context"})
def test_bind_data_index_foo_to_my_param(component):
    """
    Component configuration contains

    args:
      - my_context: context
      - my_param: data.foo

    ergo should search `message.data` for a "foo" key, and bind its value to `my_param`. If it doesn't find
    one, it should raise TypeError for a missing 'my_param' argument.
    """

    results = Queue(routing_key=component.pubtopic)
    errors = Queue(routing_key=component.error_queue_name)
    publish_pika(component.subtopic, foo="bar")
    assert results.consume()["data"] == "bar"
    publish_pika(component.subtopic, data={"foo": "bar"})
    assert results.consume()["data"] == "bar"
    publish_pika(component.subtopic, data="foo")
    error_result = errors.consume()
    assert "missing 1 required positional argument: 'my_param'" in error_result["error"]["message"]
    publish_pika(component.subtopic, something_else="bar")
    error_result = errors.consume()
    assert "missing 1 required positional argument: 'my_param'" in error_result["error"]["message"]
    publish_pika(component.subtopic, foo="bar", something_else="something else")
    assert results.consume()["data"] == "bar"


@amqp_component(handler_with_mapped_params, args={"my_context": "context"})
def test_dont_bind_data(component):
    """
    Configuration contains no argument mapping. ergo will assume that `my_param` is supposed be a key in `data`, and will
     raise TypeError if it doesn't find it there.
    """
    results = Queue(routing_key=component.pubtopic)
    errors = Queue(routing_key=component.error_queue_name)
    publish_pika(component.subtopic, data={"my_param": "bar"})
    assert results.consume()["data"] == "bar"
    publish_pika(component.subtopic, my_param="bar")
    assert results.consume()["data"] == "bar"
    publish_pika(component.subtopic, something_else="bar")
    error_result = errors.consume()
    assert "missing 1 required positional argument: 'my_param'" in error_result["error"]["message"]
