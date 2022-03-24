"""Summary."""
import datetime
import os
from typing import List

import yaml
from colors import color

from ergo.amqp_invoker import AmqpInvoker
from ergo.config import Config
from ergo.flask_http_invoker import FlaskHttpInvoker
from ergo.function_invocable import FunctionInvocable
from ergo.http_gateway import HttpGatewayServer
from ergo.http_invoker import HttpInvoker
from ergo.schematic import graph as ergograph
from ergo.version import get_version


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


def load_config(*config_paths: str) -> Config:
    unmerged_data: List[dict] = []
    paths = list(config_paths)
    for path in paths:
        with open(path, "r") as fh:
            file_data = yaml.safe_load(fh)
        if "namespace" in file_data:
            with open(file_data.pop("namespace"), "r") as fh:
                unmerged_data.insert(0, yaml.safe_load(fh))
        unmerged_data.append(file_data)
    merged_data = {}
    for config in unmerged_data:
        merged_data.update(config)
    return Config(merged_data)


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

    @staticmethod
    def gateway(ref: str) -> int:
        config = load_config(ref)
        server = HttpGatewayServer(config)
        return server.run()

    def http(self, func: str, *args: str) -> int:
        """Summary.

        Args:
            func (str): Description
            *args (str): Description

        Returns:
            int: Description

        """
        config = Config({'func': func})
        return self._http(config)

    def _http(self, config: Config):
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
        config = load_config(ref, *args)
        if config.protocol == 'amqp':
            return self.amqp(config)
        if config.protocol == 'http':
            return self._http(config)
        raise ValueError(f'unexpected protocol: {config.protocol}')

    def graph(self, *args: str) -> int:
        """Summary.

        Args:
            ref (str): root folder for graph

        Returns:
            int: Description

        """
        ergograph(list(args))
        return 0
