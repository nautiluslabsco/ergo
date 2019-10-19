from typing import List
import click
from click_default_group import DefaultGroup # https://pypi.org/project/click-default-group/
from src.ergo_cli import ErgoCli
from src.ergo_cmd import ErgoCmd

ergo_cli = ErgoCli()

@click.group(cls=DefaultGroup, default='shell', default_if_no_args=True)
def main():
  pass

@main.command()
def shell():
  ErgoCmd(ergo_cli).cmdloop()


@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def run(ref: str, arg: List[str]):
  return ergo_cli.run(ref, arg)

@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def http(ref: str, arg: List[str]):
  return ergo_cli.http(ref, arg)

@main.command()
@click.argument('ref', type=click.STRING)
@click.argument('arg', nargs=-1)
def stop(ref: str, arg: List[str]):
  return ergo_cli.stop(ref, arg)
