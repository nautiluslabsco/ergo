from ergo.message import Message

from test.integration.utils.amqp import AMQPComponent, ComponentFailure, Queue, publish


def assert_false():
    assert False


def test_no_error_pubtopic():
    component = AMQPComponent(assert_false)
    error_queue = Queue(name=component.error_queue_name)
    with component, error_queue:
        publish({}, component.subtopic)
        assert isinstance(error_queue.get(), Message)


def test_error_pubtopic():
    error_key = 'test.error_pubtopic'
    component = AMQPComponent(assert_false, error_pubtopic=error_key)
    error_queue = Queue(name=component.error_queue_name)
    error_pubtopic = Queue(routing_key=error_key)
    with component, error_queue, error_pubtopic:
        publish({}, component.subtopic)
        assert isinstance(error_queue.get(), Message)
        assert isinstance(error_pubtopic.get(), Message)
