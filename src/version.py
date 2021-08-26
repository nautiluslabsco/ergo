"""Summary.

Attributes:
    VERSION (str): Description

"""
import subprocess
import sys

VERSION = '0.4.15-alpha'


def get_version() -> str:
    """Summary.

    Returns:
        str: Description

    """
    return VERSION


# wtc && match => ok
# wtc && incr => not ok
# changes && match => not ok
# changes && incr => ok
def main() -> None:
    """Summary."""
    ver: str = get_version()
    tag: str = subprocess.check_output(['git', 'describe', '--tags']).decode('utf-8')
    status: str = subprocess.check_output(['git', 'status']).decode('utf-8')
    try:
        if tag.index(ver) == 0 and 'working tree clean' not in status:  # if version hasn't changed
            print(f'Version {VERSION} must be incremented in src/version.py because codebase has changed')
            sys.exit(1)
        else:
            # print('not status')
            # sys.exit(0)
            print(get_version())
    except ValueError:
        print(get_version())


# def main() -> None:
#     """Summary."""
#     ver: str = get_version()
#     tag: str = subprocess.check_output(['git', 'describe', '--tags']).decode('utf-8')
#     status: str = subprocess.check_output(['git', 'status']).decode('utf-8')
#     clean = 'working tree clean' in status
#     match = False
#     try:
#         match = tag.index(ver) == 0
#     except ValueError:
#         pass

#     if clean and not match or match and not clean:
#         print('Version must be incremented with changes to codebase')
#         sys.exit(1)
#     else:
#         print(get_version())


if __name__ == '__main__':
    main()
