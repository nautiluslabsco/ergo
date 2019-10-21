"""Summary."""
import cmd  # https://docs.python.org/3/library/cmd.html
from typing import IO, List, Optional

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

    def do_exit(self, line: str) -> int:
        """Summary.

        Args:
            line (str): Description

        Returns:
            int: Description

        """
        return 1

    def do_run(self, line: str) -> int:
        """Summary.

        Args:
            line (str): Description

        Returns:
            int: Description

        """
        args: List[str] = line.split()
        return self._cli.run(args[0], *args[1:])

    def do_http(self, line: str) -> int:
        """Summary.

        Args:
            line (str): Description

        Returns:
            int: Description

        """
        args: List[str] = line.split()
        return self._cli.http(args[0], *args[1:])
