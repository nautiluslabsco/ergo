import multiprocessing
import functools
from typing import Callable
from src.ergo_cli import ErgoCli


def with_ergo(command: str, *ergo_args: str):
    """
    This decorator adds setup code to the wrapped function that starts a temporary ergo worker in a child process.
    The worker is terminated prior to the wrapped function returning.

    Args:
        command (str): An ergo command, e.g. start, amqp or http.
        *ergo_args (str): Positional arguments to pass to ergo.
    :return:
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            ergo_process = multiprocessing.Process(
                target=getattr(ErgoCli(), command),
                args=ergo_args,
            )
            ergo_process.start()
            try:
                ret = fn(*args, **kwargs)
            finally:
                ergo_process.terminate()
            return ret
        return wrapped
    return decorator
