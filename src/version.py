"""Summary.

Attributes:
    VERSION (str): Description

"""
import subprocess
import sys

VERSION = '0.3.26-alpha'


def get_version() -> str:
    """Summary.

    Returns:
        str: Description

    """
    return VERSION


if __name__ == '__main__':
    ver: str = get_version()
    tag: str = subprocess.check_output(['git', 'describe', '--tags']).decode('utf-8')
    status: str = subprocess.check_output(['git', 'status']).decode('utf-8')
    try:
        if tag.index(ver) == 0 and status:  # if version hasn't changed
            print('Version must be incremented if with changes to codebase')
            sys.exit(1)
        else:
            # print('not status')
            # sys.exit(0)
            print(get_version())
    except ValueError:
        print(get_version())
