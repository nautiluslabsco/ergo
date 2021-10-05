import multiprocessing
from contextlib import contextmanager
from src.ergo_cli import ErgoCli


@contextmanager
def run(manifest, namespace):
    """
    This context manager starts a temporary ergo worker in a subprocess. The worker is terminated at __exit__ time.
    """
    process = multiprocessing.Process(target=ErgoCli().start, args=(manifest, namespace,))
    process.start()
    try:
        yield
    finally:
        process.terminate()
