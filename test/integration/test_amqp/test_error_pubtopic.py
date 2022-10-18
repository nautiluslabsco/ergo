from ergo.message import Message

from test.integration.utils.amqp import AMQPComponent, Queue, publish


def assert_false():
    assert False


def test_no_error_pubtopic():
    component = AMQPComponent(assert_false)
    error_queue = Queue(name=component.error_queue_name, auto_delete=False)
    with component, error_queue:
        publish({}, component.subtopic)
        error_message = error_queue.get()

        assert isinstance(error_message, Message)
        assert error_message.error['type'] == 'AssertionError'


def test_error_pubtopic():
    error_key = 'test.error_pubtopic'
    component = AMQPComponent(assert_false, error_pubtopic=error_key)
    error_queue = Queue(name=component.error_queue_name, auto_delete=False)
    error_pubtopic = Queue(routing_key=error_key)
    with component, error_queue, error_pubtopic:
        publish({}, component.subtopic)

        error_queue_message = error_queue.get()
        assert isinstance(error_queue_message, Message)
        assert error_queue_message.error['type'] == 'AssertionError'

        error_pubtopic_message = error_pubtopic.get()
        assert isinstance(error_pubtopic_message, Message)
        assert error_pubtopic_message.error['type'] == 'AssertionError'
