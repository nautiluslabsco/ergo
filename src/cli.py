import click
import json
from typing import List, Optional
from src.flask_http_invoker import FlaskHttpInvoker
from src.function_invocable import FunctionInvocable
import subprocess
import re
import cmd # https://docs.python.org/3/library/cmd.html

class ErgoCli(object):
  def run(self, reference: str, argv: List = []):
    host = FunctionInvocable(reference)
    result = []
    host.invoke(argv, result)
    return str(result)
cli = ErgoCli()



class ErgoShell(cmd.Cmd):
  intro = 'Welcome to the ergo shell. Type help or ? to list commands.\n'
  prompt = 'ergo ∴ '

  @staticmethod
  def parse(arg):
      'Convert a series of zero or more numbers to an argument tuple'
      return list(map(str, arg.split()))

  def do_exit(self, arg):
    'Exit'
    print('ergo shell terminated')
    return True

  def do_run(self, arg):
    args = ErgoShell.parse(arg)
    print(cli.run(args[0], args[1:]))

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
  host = FlaskHttpInvoker(FunctionInvocable(reference))
  host.start()

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
