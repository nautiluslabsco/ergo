"""Summary."""
import datetime
import os

import yaml
from colors import color

from src.amqp_invoker import AmqpInvoker
from src.config import Config
from src.flask_http_invoker import FlaskHttpInvoker
from src.function_invocable import FunctionInvocable
from src.http_invoker import HttpInvoker
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
        return f'{color("ergo", fg="#33ff33")} {color("∴", fg="#33ff33")} '
        # return 'ergo ∴ '

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

    def run(self, config: Config, *args: str) -> int:
        """Summary.

        Args:
            config (str): Description
            *args (str): Description

        Returns:
            int: Description

        Raises:
            err: Description

        """
        try:
            host: FunctionInvocable = FunctionInvocable(config)
            for result in host.invoke(dict(zip([str(i) for i in range(len(args))], args))):
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

    def http(self, config: Config, *args: str) -> int:
        """Summary.

        Args:
            config (str): Description
            *args (str): Description

        Returns:
            int: Description

        """
        host: HttpInvoker = FlaskHttpInvoker(FunctionInvocable(config))
        host.start()
        return 0

    def amqp(self, config: Config, *args: str) -> int:
        """Summary.

        Args:
            ref (str): Description
            *args (str): Description

        Returns:
            int: Description

        """
        host: AmqpInvoker = AmqpInvoker(FunctionInvocable(config))
        host.start()
        return 0

    def start(self, ref: str, *args: str) -> int:
        """Summary.

        Args:
            ref (str): Description
            *args (str): Description

        Returns:
            int: Description

        """
        # use safe_load instead load
        with open(ref) as config_file:
            conf = yaml.safe_load(config_file)
            namespace_file_name = args[0] if len(args) > 0 else conf.get('namespace')
            with open(namespace_file_name) as namespace_file:
                namespace_cfg = yaml.safe_load(namespace_file)
                conf.update(namespace_cfg)
                config = Config(conf)

                return {'amqp': self.amqp, 'something_else': self.http}.get(config.protocol, self.http)(config)
