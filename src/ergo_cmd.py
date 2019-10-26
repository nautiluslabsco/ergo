"""Summary."""
import cmd  # https://docs.python.org/3/library/cmd.html
from typing import IO, Callable, List, Optional, cast

from src.ergo_cli import ErgoCli


class ErgoCmd(cmd.Cmd):
    """Summary."""

    intro: str = ''
    prompt: str = ''

    def __init__(self, cli: ErgoCli, completekey: str = 'tab', stdin: Optional[IO[str]] = None, stdout: Optional[IO[str]] = None) -> None:
        """Summary.

        Args:
            cli (ErgoCli): Description
            completekey (str, optional): Description
            stdin (Optional[IO[str]], optional): Description
            stdout (Optional[IO[str]], optional): Description

        """
        super().__init__(completekey, stdin, stdout)
        self._cli = cli
        ErgoCmd.intro = self._cli.intro
        ErgoCmd.prompt = self._cli.prompt

    def onecmd(self, line: str) -> bool:
        """Summary.

        Args:
            line (TYPE): Description

        Returns:
            TYPE: Description

        """
        splitline: List[str] = line.split()
        command: str = splitline[0]
        if hasattr(self, f'do_{command}') or not hasattr(self._cli, command):
            return super().onecmd(line)

        args: List[str] = splitline[1:]
        return cast(Callable[[str], bool], getattr(self._cli, command))(args[0], *args[1:])

    def do_exit(self, line: str) -> bool:
        """Summary.

        Args:
            line (str): Description

        Returns:
            int: Description

        """
        return True
