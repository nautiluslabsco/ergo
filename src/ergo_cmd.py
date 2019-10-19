import cmd # https://docs.python.org/3/library/cmd.html

class ErgoCmd(cmd.Cmd):
  intro = None
  prompt = None
  def __init__(self, cli, *args, **kwargs):
    super().__init__(args, kwargs)
    self._cli = cli
    ErgoCmd.intro = self._cli.intro
    ErgoCmd.prompt = self._cli.prompt

  def onecmd(self, line):
    try:
      return super().onecmd(line)
    except Exception as err:
      print(f'*** {err}')
      # traceback.print_exc(file=sys.stdout)
      return False # don't stop

  def do_exit(self, line):
    return True

  def do_run(self, line):
    args = line.split()
    return self._cli.run(args[0], args[1:])

  def do_http(self, line):
    args = line.split()
    return self._cli.http(args[0], args[1:])