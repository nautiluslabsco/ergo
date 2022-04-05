from test.integration.utils.amqp import AMQPComponent, ComponentFailure, Queue, publish

import pytest

from ergo.context import Context

"""
These tests assert that ergo can correctly bind message data to a custom parameter using the `args` configuration attribute.
"""


def handler_with_mapped_params(my_context: Context, my_param):
    assert isinstance(my_context, Context)
    return my_param


def test_bind_data_to_my_param():
    """
    Component configuration contains

    args:
      - my_context: context
      - my_param: data

    ergo should bind the full payload to `my_param`
    """
    component = AMQPComponent(handler_with_mapped_params, args={"my_param": "data", "my_context": "context"})
    results = Queue(routing_key=component.pubtopic)
    with component, results:
        publish({"foo": "bar"}, component.subtopic)
        assert results.consume().data == {"foo": "bar"}
        publish({"data": {"foo": "bar"}}, component.subtopic)
        assert results.consume().data == {"foo": "bar"}
        publish({"data": "foo"}, component.subtopic)
        assert results.consume().data == "foo"
        publish({"something_else": "bar"}, component.subtopic)
        assert results.consume().data == {"something_else": "bar"}


def test_bind_data_index_foo_to_my_param():
    """
    Component configuration contains

    args:
      - my_context: context
      - my_param: data.foo

    ergo should search `message.data` for a "foo" key, and bind its value to `my_param`. If it doesn't find
    one, it should raise TypeError for a missing 'my_param' argument.
    """
    component = AMQPComponent(handler_with_mapped_params, args={"my_param": "data.foo", "my_context": "context"})
    results = Queue(routing_key=component.pubtopic)
    with component, results:
        publish({"foo": "bar"}, component.subtopic)
        assert results.consume().data == "bar"
        publish({"data": {"foo": "bar"}}, component.subtopic)
        assert results.consume().data == "bar"
        with pytest.raises(ComponentFailure):
            try:
                publish({"data": "foo"}, component.subtopic)
                results.consume()
            except Exception as e:
                assert "missing 1 required positional argument: 'my_param'" in str(e)
                raise
        with pytest.raises(ComponentFailure):
            try:
                publish({"something_else": "bar"}, component.subtopic)
                results.consume()
            except Exception as e:
                assert "missing 1 required positional argument: 'my_param'" in str(e)
                raise


def test_dont_bind_data():
    """
    Configuration contains no argument mapping. ergo will assume that `my_param` is supposed be a key in `data`, and will
     raise TypeError if it doesn't find it there.
    """
    component = AMQPComponent(handler_with_mapped_params, args={"my_context": "context"})
    results = Queue(routing_key=component.pubtopic)
    with component, results:
        publish({"data": {"my_param": "bar"}}, component.subtopic)
        assert results.consume().data == "bar"
        publish({"my_param": "bar"}, component.subtopic)
        assert results.consume().data == "bar"
        with pytest.raises(ComponentFailure):
            try:
                publish({"something_else": "bar"}, component.subtopic)
                results.consume()
            except Exception as e:
                assert "missing 1 required positional argument: 'my_param'" in str(e)
                raise
