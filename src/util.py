"""Convenience Funcs for handling errors, logging, and monitoring."""
import importlib.util
import os
import re
import sys
import time
import traceback
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from types import FrameType, ModuleType, TracebackType
from typing import Any, List, Match, Optional
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


def load_source(ref: str) -> Any:
    pattern: str = r'^(.*\/)?([^\.\/]+)\.([^\.]+):([^:]+\.)?([^:\.]+)$'
    matches: Optional[Match[str]] = re.match(pattern, ref)
    if not matches:
        raise Exception(f'Invalid source reference pattern {ref}, must conform to [path/to/file/]<file>.<extension>[:[class.]method]]')

    path_to_source_file: str = matches.group(1)
    if not matches.group(1):
        path_to_source_file = os.getcwd()
    elif matches.group(1)[0] != '/':
        path_to_source_file = f'{os.getcwd()}/{matches.group(1)}'
    source_file_name: str = matches.group(2)
    source_file_extension: str = matches.group(3)
    sys.path.insert(0, path_to_source_file)

    spec: ModuleSpec = importlib.util.spec_from_file_location(source_file_name, f'{path_to_source_file}/{source_file_name}.{source_file_extension}')
    module: ModuleType = importlib.util.module_from_spec(spec)
    assert isinstance(spec.loader, Loader)  # see https://github.com/python/typeshed/issues/2793
    spec.loader.exec_module(module)

    scope: ModuleType = module
    match = matches.group(4)
    if match is not None:
        class_name: str = match[:-1]
        scope = getattr(scope, class_name)

    method_name: str = matches.group(5)
    return getattr(scope, method_name)
