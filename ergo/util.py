"""Convenience Funcs for handling errors, logging, and monitoring."""
import re
import signal
import sys
import threading
import time
import traceback
from functools import lru_cache
from types import FrameType, TracebackType
from typing import List, Optional, Tuple
from uuid import uuid4

if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=C0412
else:
    from typing_extensions import TypedDict  # pragma: no cover


class LogStruct(TypedDict):
    """Summary."""

    ts: float
    mid: str
    cid: str


def log(rec: List[LogStruct]) -> List[LogStruct]:
    """Summary.

    Args:
        rec (List[Dict[str, Any]]): Description

    Returns:
        List[Dict[str, Any]]: Description
    """
    cid: str = uniqueid()
    if rec:
        cid = rec[-1].get('cid', cid)
    rec.append(LogStruct({'ts': timestamp(), 'mid': uniqueid(), 'cid': cid}))
    return rec


def uniqueid() -> str:
    """Generate unique id.

    Returns:
        str: unique hex id
    """
    return uuid4().hex


def timestamp() -> float:
    """Create timestamp for current time.

    Returns:
        int: current time
    """
    return time.time()


def get_stack() -> List[FrameType]:
    """Summary.

    Returns:
        List[FrameType]: Description
    """
    frm: Optional[FrameType] = None
    trcbk: Optional[TracebackType] = sys.exc_info()[2]
    while trcbk:
        if not trcbk.tb_next:
            frm = trcbk.tb_frame
            break
        trcbk = trcbk.tb_next  # pragma: no cover
    stack: List[FrameType] = []
    while frm:
        stack.append(frm)
        frm = frm.f_back
    return stack


def print_exc_plus() -> str:  # pragma: no cover
    """
    Summary.

    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.

    Returns:
        str: Description
    """
    ret = ''
    stack = get_stack()
    stack.reverse()
    ret = f'{ret}\n{traceback.format_exc()}'
    ret = f'{ret}\nLocals by frame, innermost last'
    for frame in stack:
        ret = f'{ret}\nFrame {frame.f_code.co_name} in {frame.f_code.co_filename} at line {frame.f_lineno}'
        for key, value in frame.f_locals.items():
            ret = f'{ret}\n\t{key} = '
            # We have to be VERY careful not to cause a new error in our error
            # printer! Calling str(  ) on an unknown object could cause an
            # error we don't want, so we must use try/except to catch it --
            # we can't stop it from happening, but we can and should
            # stop it from propagating if it does happen!
            try:
                ret = f'{ret}\n{value}'
            except BaseException:  # pylint: disable=broad-except
                ret = f'{ret}\n<ERROR WHILE PRINTING VALUE>'

    return ret


def extract_from_stack(exc: BaseException) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract minimal useful information from top of function stack.

    Returns:
        str: filename
        str: lineno
        str: function name
    """
    traceback_exception = traceback.TracebackException.from_exception(exc)
    stack_string = traceback_exception.stack.format()[-1]
    # File ".*", line n+, in s+\n
    prog = re.compile(r'File ".+/(\w+[.]py)", line (\d+), in (\w+)\n')
    match = prog.search(stack_string)
    if match:
        matches = match.groups()
        if len(matches) == 3:  # for mypy
            return matches[0], matches[1], matches[2]
    return None, None, None


_shutdown = threading.Event()
_termination_pending = threading.Event()


class defer_termination:
    """
    Use this context manager to temporarily postpone shutdown via SIGTERM.
    """

    def __enter__(self):
        if _termination_pending.is_set():
            _shutdown.wait()
        self._signum = None
        signal.signal(signal.SIGTERM, self._sigterm_handler)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.signal(signal.SIGTERM, 0)
        if self._signum:
            signal.raise_signal(self._signum)

    def _sigterm_handler(self, signum, _):
        _termination_pending.set()
        self._signum = signum


@lru_cache(1)
def instance_id() -> str:
    return uniqueid()
