"""Summary.

Attributes:
    ERGO_CLI (TYPE): Description

"""
from typing import Tuple

import click
from click_default_group import \
    DefaultGroup  # https://pypi.org/project/click-default-group/

from src.config import Config
from src.ergo_cli import ErgoCli
from src.ergo_cmd import ErgoCmd

ERGO_CLI = ErgoCli()


@click.group(cls=DefaultGroup, default='shell', default_if_no_args=True)
def main() -> int:
    """Summary."""


@main.command()
def shell() -> int:
    """Summary.

    Returns:
        int: Description

    """
    ErgoCmd(ERGO_CLI).cmdloop()
    return 0


@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def run(config: Config, arg: Tuple[str]) -> int:
    """Summary.

    Args:
        config (str): Description
        arg (Tuple[str]): Description

    Returns:
        int: Description

    """
    return ERGO_CLI.run(config, *list(arg))


@main.command()
@click.argument('name', type=click.STRING)
def init(name: str) -> int:
    """Summary.

    Args:
        name (str): Description

    Returns:
        int: Description

    """
    return ERGO_CLI.init(name)


@main.command()
@click.argument('name', type=click.STRING)
def use(name: str) -> int:
    """Summary.

    Args:
        name (str): Description

    Returns:
        int: Description

    """
    return ERGO_CLI.use(name)


@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def http(config: Config, arg: Tuple[str]) -> int:
    """Summary.

    Args:
        config (str): Description
        arg (Tuple[str]): Description

    Returns:
        int: Description

    """
    return ERGO_CLI.http(config, *list(arg))


@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def amqp(config: Config, arg: Tuple[str]) -> int:
    """Summary.

    Args:
        config (str): Description
        arg (Tuple[str]): Description

    Returns:
        int: Description

    """
    return ERGO_CLI.amqp(config, *list(arg))


@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def start(ref: str, arg: Tuple[str]) -> int:
    """Summary.

    Args:
        ref (str): Description
        arg (Tuple[str]): Description

    Returns:
        int: Description

    """
    return ERGO_CLI.start(ref, *list(arg))
