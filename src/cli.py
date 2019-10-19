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
from click_default_group import DefaultGroup # https://pypi.org/project/click-default-group/
from colors import *
from src.version import get_version
import traceback
import sys

class ErgoCli(object):
  def quit(self):
    return True
  
  def run(arg: str):
    argv = arg
    if type(arg) is tuple:
      argv = ''.join(list(arg))
    argv = argv.split()
    result = []
    host = FunctionInvocable(argv[0])
    host.invoke(argv[1:], result)
    print(str(result))

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
  return os.path.dirname(os.path.abspath(__file__)) + "/version.py"


class ErgoShell(cmd.Cmd):
  intro = color(f'ergo {get_version()} ({fd(os.path.getmtime(get_version_path()))})\nType help or ? to list commands.', fg='#ffffff')
  prompt = f'{color("ergo", fg="#33ff33")} {color("∴", fg="#33ff33")} '

  def __init__(self, cli, *args, **kwargs):
    super().__init__(args, kwargs)
    self._cli = cli

  def onecmd(self, line):
      try:
          cmd = line.split(' ', 2)
          # method = globals()['_%s' % cmd[0]]
          method = getattr(self._cli, cmd[0])
          method(str(cmd[1])) #super().onecmd(line)
          return False
      except Exception as err:
          try:
            return super().onecmd(line)
          except:
            print(f'*** {err}')
            traceback.print_exc(file=sys.stdout)
            return False # don't stop

@click.group(cls=DefaultGroup, default='shell', default_if_no_args=True)
def main():
  pass

@main.command()
def shell():
  # setattr(ErgoShell, 'do_run', ErgoCli.run)
  es = ErgoShell(cli)
  es.cmdloop()

@main.command()
@click.argument('reference', type=click.STRING) # a function referenced by <module>[.<class>][:<function>]
def stdio(reference: str):
  pass

@main.command()
@click.argument('arg', nargs=-1)
def run(arg: str):
  return cli.run(arg)



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
