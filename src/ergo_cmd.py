import cmd  # https://docs.python.org/3/library/cmd.html
from typing import IO, Optional

from src.ergo_cli import ErgoCli


class ErgoCmd(cmd.Cmd):
    intro: str = ''
    prompt: str = ''

    def __init__(self, cli: ErgoCli, completekey: str = 'tab', stdin: Optional[IO[str]] = None, stdout: Optional[IO[str]] = None) -> None:
        super().__init__(completekey, stdin, stdout)
        self._cli = cli
        ErgoCmd.intro = self._cli.intro
        ErgoCmd.prompt = self._cli.prompt

    # def onecmd(self, line):
    #   try:
    #     return super().onecmd(line)
    #   except Exception as err:
    #     print(f'*** {err}')
    #     traceback.print_exc(file=sys.stdout)
    #     return False  # don't stop

    def do_exit(self, line: str) -> bool:
        return True

    def do_run(self, line: str) -> bool:
        args = line.split()
        return self._cli.run(args[0], *args[1:])

    def do_http(self, line: str) -> bool:
        args = line.split()
        return self._cli.http(args[0], *args[1:])
