import click
import json
from typing import List, Optional
from src.flask_http_invoker import FlaskHttpInvoker
from src.function_invocable import FunctionInvocable
import subprocess
import re
import os
import datetime
import cmd # https://docs.python.org/3/library/cmd.html

from colors import *

class ErgoCli(object):
  def quit(self):
    return True

  def run(self, reference: str, argv: List = []):
    host = FunctionInvocable(reference)
    result = []
    host.invoke(argv, result)
    return str(result)

  def http(self, reference: str):
    host = FlaskHttpInvoker(FunctionInvocable(reference))
    host.start()


cli = ErgoCli()

def from_file(file_name):
  """print long description"""
  with open(file_name) as f:
    return f.read().strip()

def fd(seconds):
  return datetime.datetime.fromtimestamp(seconds).strftime('%b %d %Y, %H:%M:%S.%f')[:-3]

def get_version_path():
  return os.path.dirname(os.path.abspath(__file__)) + "/../VERSION"

class ErgoShell(cmd.Cmd):
  intro = color(f'ergo {from_file(get_version_path())} ({fd(os.path.getmtime(get_version_path()))})\nType help or ? to list commands.', fg='#ffffff')
  prompt = f'{color("ergo", fg="#ffb000")} {color("∴", fg="#ffb000")} '

  def do_quit(self, arg):
    return cli.quit()

  def do_exit(self, arg):
    return cli.quit()

  def do_run(self, arg):
    args = arg.split()
    print(cli.run(args[0], args[1:]))

  def do_http(self, arg):
    cli.http(arg)

@click.group()
def main():
  pass

@main.command()
def shell():
  ErgoShell().cmdloop()

@main.command()
@click.argument('reference', type=click.STRING) # a function referenced by <module>[.<class>][:<function>]
def stdio(reference: str):
  pass

@main.command()
@click.argument('reference', type=click.STRING) # a function referenced by <module>[.<class>][:<function>]
@click.argument('argv', nargs=-1)
def run(reference: str, argv: List):
  click.echo(cli.run(reference, argv))

@main.command()
@click.argument('reference', type=click.STRING) # a function referenced by <module>[.<class>][:<function>]
def http(reference: str):
  cli.http(reference)

@main.command()
@click.argument('scope', type=click.STRING, required=False) # major, minor, patch
def version(scope: Optional[str] = None):
  tag = None
  try:
    tag = subprocess.check_output(["git", "describe", "--tags"]).decode('ascii').strip()
  except subprocess.CalledProcessError:
    print('no previous version')
    exit(0)

  pattern: str = r'([0-9]+)\.([0-9]+)\.([0-9]+)(\-alpha)?(\-.*)?'
  matches = re.match(pattern, tag)

  if not scope:
    print(f'{matches.group(1)}.{matches.group(2)}.{matches.group(3)}{matches.group(4)}')
    exit(0)


  verdict: Dict[str, [int, str]] = {
    'major': int(matches.group(1)),
    'minor': int(matches.group(2)),
    'patch': int(matches.group(3)),
    'build': matches.group(4)
  }
  verdict[scope] += 1

  new_version = f'{verdict["major"]}.{verdict["minor"]}.{str(verdict["patch"]).zfill(2)}{verdict["build"]}'
  subprocess.check_call(["git", "tag", new_version])
  subprocess.check_call(["git", "push", "--tags"])
