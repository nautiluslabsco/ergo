import datetime
import os

from colors import *

from src.flask_http_invoker import FlaskHttpInvoker
from src.function_invocable import FunctionInvocable
from src.version import get_version


def fd(seconds):
    return datetime.datetime.fromtimestamp(seconds).strftime('%b %d %Y, %H:%M:%S.%f')[:-3]


def get_version_path():
    return os.path.dirname(os.path.abspath(__file__)) + "/version.py"


class ErgoCli(object):
    @property
    def prompt(self):
        return f'{color("ergo", fg="#33ff33")} {color("∴", fg="#33ff33")} '

    @property
    def intro(self):
        return color(f'ergo {get_version()} ({fd(os.path.getmtime(get_version_path()))})\nType help or ? to list commands.', fg='#ffffff')

    def run(self, ref, *args):
        try:
            result = []
            host = FunctionInvocable(ref)
            host.invoke(result, *args)
            print(result)
        except Exception as err:
            print(f'*** {err}')
            raise (err)
        return False

    def http(self, ref, *args):
        host = FlaskHttpInvoker(FunctionInvocable(ref))
        host.start()
        return False
