import multiprocessing
import functools
from typing import Callable, Optional
from src.ergo_cli import ErgoCli


def with_ergo(command: str, target: str, namespace: Optional[str] = None):
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            ergo_process = multiprocessing.Process(
                target=getattr(ErgoCli(), command),
                args=(target, namespace,),
            )
            ergo_process.start()
            try:
                ret = fn(*args, **kwargs)
            finally:
                ergo_process.terminate()
            return ret
        return wrapped
    return decorator
