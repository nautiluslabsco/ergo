from typing import Tuple

import click
from click_default_group import \
    DefaultGroup  # https://pypi.org/project/click-default-group/

from src.ergo_cli import ErgoCli
from src.ergo_cmd import ErgoCmd

ERGO_CLI = ErgoCli()


@click.group(cls=DefaultGroup, default='shell', default_if_no_args=True)
def main() -> int:
    pass


@main.command()
def shell() -> int:
    ErgoCmd(ERGO_CLI).cmdloop()
    return 0


@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def run(ref: str, arg: Tuple[str]) -> int:
    return ERGO_CLI.run(ref, *list(arg))


@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def http(ref: str, arg: Tuple[str]) -> int:
    return ERGO_CLI.http(ref, *list(arg))
