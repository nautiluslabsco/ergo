"""Summary."""
import sys
import traceback
from types import FrameType, TracebackType
from typing import List, Optional


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
        trcbk = trcbk.tb_next
    stack: List[FrameType] = []
    while frm:
        stack.append(frm)
        frm = frm.f_back
    return stack


def print_exc_plus() -> str:
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
