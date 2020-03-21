"""Summary."""
import datetime
import os

from colors import color

from src.flask_http_invoker import FlaskHttpInvoker
from src.function_invocable import FunctionInvocable
from src.http_invoker import HttpInvoker
from src.payload import Payload
from src.version import get_version


def format_date(sec: float) -> str:
    """Summary.

    Args:
        sec (float): Description

    Returns:
        str: Description

    """
    dtf: str = '%b %d %Y, %H:%M:%S.%f'
    return datetime.datetime.fromtimestamp(sec).strftime(dtf)[:-3]


def get_version_path() -> str:
    """Summary.

    Returns:
        str: Description

    """
    return os.path.dirname(os.path.abspath(__file__)) + '/version.py'


class ErgoCli:
    """Summary."""

    @property
    def prompt(self) -> str:
        """Summary.

        Returns:
            str: Description

        """
        # return f'{color("ergo", fg="#33ff33")} {color("∴", fg="#33ff33")} '
        return 'ergo ∴ '

    @property
    def intro(self) -> str:
        """Summary.

        Returns:
            str: Description

        """
        version: str = get_version()
        timestamp: str = format_date(os.path.getmtime(get_version_path()))
        intro: str = f'ergo {version} ({timestamp})\nType help or ? to list commands.'

        return str(color(intro, fg='#ffffff'))

    def run(self, ref: str, *args: str) -> int:
        """Summary.

        Args:
            ref (str): Description
            *args (str): Description

        Returns:
            int: Description

        Raises:
            err: Description

        """
        try:
            result: Payload = Payload()
            host: FunctionInvocable = FunctionInvocable(ref)
            host.invoke(result, Payload(dict(zip([str(i) for i in range(len(args))], args))))
            print(str(result))
        except Exception as err:
            print(f'*** {err}')
            raise err
        return 0

    def use(self, name: str) -> int:
        """Summary.

        Args:
            name (str): Description

        Returns:
            int: Description

        """
        with open('.ergo/HEAD', 'w') as file:
            file.write(f'{name}\n')

        return 0

    def init(self, name: str) -> int:
        """Summary.

        Args:
            name (str): Description

        Returns:
            int: Description

        """
        try:
            os.makedirs(f'.ergo/{name}')
        except FileExistsError:
            pass
        self.use(name)
        return 0

    def http(self, ref: str, *args: str) -> int:
        """Summary.

        Args:
            ref (str): Description
            *args (str): Description

        Returns:
            int: Description

        """
        host: HttpInvoker = FlaskHttpInvoker(FunctionInvocable(ref))
        host.start()
        return 0
