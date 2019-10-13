import click
import json
from typing import List
from src.function_host import FunctionHost

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
	# data_in: Dict[str, Any] = json.loads(argv)
	host = FunctionHost(reference)
	result = []
	host.invoke(argv, result) # 32.4
	click.echo(str(result))
