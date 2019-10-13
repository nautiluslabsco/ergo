import click
import json
from typing import List
from src.flask_http_invoker import FlaskHttpInvoker
from src.function_invocable import FunctionInvocable

@click.group()
def main():
    pass

@main.command()
@click.argument('reference', type=click.STRING) # a function referenced by <module>[.<class>][:<function>]
def stdio(reference: str):
	pass

@main.command()
@click.argument('reference', type=click.STRING) # a function referenced by <module>[.<class>][:<function>]
@click.argument('argv', nargs=-1)
def run(reference: str, argv: List):
	host = FunctionInvocable(reference)
	result = []
	host.invoke(argv, result) # 32.4
	click.echo(str(result))

@main.command()
@click.argument('reference', type=click.STRING) # a function referenced by <module>[.<class>][:<function>]
def http(reference: str):
	host = FlaskHttpInvoker(FunctionInvocable(reference))
	host.start()
