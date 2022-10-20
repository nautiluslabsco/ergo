from typing import Any, Dict

from ergo.message import Message

from test.integration.utils.amqp import AMQPComponent, Queue, publish


class MyException(Exception):
    def __init__(self, error_message: str, extra_error_info: Dict[str, Any]):
        super().__init__(self, error_message)
        self.extra_error_info = extra_error_info


def function_with_error():
    raise MyException(
        'my error message',
        {
            'int_info': 123,
            'str_info': 'onetwothree',
        },
    )


def check_error_message(error_message):
    assert isinstance(error_message, Message)
    assert error_message.error['type'] == 'MyException'
    assert 'my error message' in error_message.error['message']
    assert error_message.extra_error_info['int_info'] == 123
    assert error_message.extra_error_info['str_info'] == 'onetwothree'


def test_extra_error_info():
    component = AMQPComponent(function_with_error)
    error_queue = Queue(name=component.error_queue_name, auto_delete=False)
    with component, error_queue:
        publish({}, component.subtopic)
        error_message = error_queue.get()
        check_error_message(error_message)


def test_extra_error_info_with_error_pubtopic():
    error_key = 'test.error_pubtopic'
    component = AMQPComponent(function_with_error, error_pubtopic=error_key)
    error_queue = Queue(name=component.error_queue_name, auto_delete=False)
    error_pubtopic = Queue(routing_key=error_key)
    with component, error_queue, error_pubtopic:
        publish({}, component.subtopic)

        error_queue_message = error_queue.get()
        check_error_message(error_queue_message)

        error_pubtopic_message = error_pubtopic.get()
        check_error_message(error_pubtopic_message)
