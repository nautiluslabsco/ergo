"""Summary."""
import importlib.util
import inspect
import os
import re
import sys
import warnings
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Callable, Generator, Match, Optional

import pydash

from ergo.config import Config
from ergo.context import Context, Envelope
from ergo.message import Message
from ergo.scope import Scope
from ergo.topic import Topic
from ergo.types import TYPE_RETURN
from ergo.util import instance_id, print_exc_plus

DATA_KEY = "data"
CONTEXT_KEY = "context"


class FunctionInvocable:
    """Summary."""

    def __init__(self, config: Config) -> None:
        """Summary.

        Args:
            reference (str): Description

        """
        self._func: Optional[Callable[..., TYPE_RETURN]] = None  # type: ignore
        self._params: dict = {}
        self._config: Config = config
        self.inject()

    @property
    def config(self) -> Config:
        """Summary.

        Returns:
            Config: Description

        """
        return self._config

    @property
    def func(self) -> Optional[Callable[..., TYPE_RETURN]]:  # type: ignore
        """Summary.

        Returns:
            Optional[Callable[..., TYPE_RETURN]]: Description

        """
        return self._func

    @func.setter
    def func(self, arg: Callable[..., TYPE_RETURN]) -> None:  # type: ignore
        """Summary.

        Args:
            arg (Callable[..., TYPE_RETURN]): Description

        """
        self._func = arg

    def invoke(self, message_in: Message) -> Generator[Message, None, None]:
        """Invoke injected function.

        If func is a generator, will exhaust generator, yielding each response.
        If an exception occurs will re-raise with a stack trace.
        Func responses will not be percolated if they return None.

        Args:
            message_in (ergo.message.Message): Contents will be passed to injected function as keyword args.

        Raises:
            Exception: caught exception re-raised with a stack trace.

        """
        if not self._func:
            raise Exception('Cannot execute injected function')
        try:
            ctx = Context(message=message_in, config=self.config)
            kwargs = self.assemble_arguments(message_in, ctx)
            results = self._func(**kwargs)
            if not inspect.isgenerator(results):
                results = [results]
            for data_out in results:
                envelope = None
                if isinstance(data_out, Envelope):
                    envelope = data_out
                    data_out = envelope.data
                scope = ctx._scope
                if Topic(f"{self.config.subtopic}.{instance_id()}").overlap(Topic(scope.reply_to)):
                    # The current scope was initiated in conjunction with a request that was addressed to this
                    # component or instance. We assume that by handling this message we've resolved
                    # the request, and may exit the current scope before proceeding. This frees handlers from
                    # needing to manually exit scope after receiving a request, or else publishing messages
                    # which will be routed back to them unto eternity.
                    assert scope.parent
                    scope = scope.parent
                if envelope and envelope.topic:
                    key = envelope.topic
                else:
                    key = self.config.pubtopic
                    if ctx.pubtopic != self.config.pubtopic:
                        key = ctx.pubtopic
                        warnings.warn("Context.pubtopic is going to be immutable in a future version of ergo. Use Context.envelope to override pubtopic.", category=DeprecationWarning)
                if envelope and envelope.reply_to:
                    scope = Scope(parent=scope)
                    scope.reply_to = envelope.reply_to
                elif scope.reply_to:
                    key = f"{key}.{scope.reply_to}"
                yield Message(data=data_out, scope=scope, key=key)

        except BaseException as err:
            raise Exception(print_exc_plus()) from err

    def assemble_arguments(self, message: Message, context: Context) -> dict:
        """
        assemble_arguments maps a message and a context to a dictionary of keyword arguments to pass to this invoker's
        handler.
        """
        kwargs = {}
        # this is the complete collection of data that this invoker's handler has access to
        exposed_data = {CONTEXT_KEY: context, DATA_KEY: message.data}
        for param, default in self._params.items():
            # ergo's canonical name for this param, which the configuration may have a custom mapping for
            ergo_param_name = self.config.args.get(param, param)
            argument = pydash.get(exposed_data, ergo_param_name) or pydash.get(exposed_data, f"{DATA_KEY}.{ergo_param_name}") or default
            # MissingArgument indicates that `param` is a positional parameter that we've failed to bind an argument
            # to, either because no argument was provided or because one was given the wrong name.
            if argument is not MissingArgument:
                kwargs[param] = argument
        return kwargs

    def inject(self) -> None:
        """Summary.

        Raises:
            Exception: Description

        """
        # [path/to/file/]<file>.<extension>[:[class.]method]]
        pattern: str = r'^(.*\/)?([^\.\/]+)\.([^\.]+):([^:]+\.)?([^:\.]+)$'  # (path/to/file/)(file).(extension):(method)
        matches: Optional[Match[str]] = re.match(pattern, self._config.func)
        if not matches:
            raise Exception(f'Unable to inject invalid referenced function {self._config.func}')

        path_to_source_file: str = matches.group(1)
        if not matches.group(1):
            path_to_source_file = os.getcwd()
        elif matches.group(1)[0] != '/':
            path_to_source_file = f'{os.getcwd()}/{matches.group(1)}'
        source_file_name: str = matches.group(2)
        source_file_extension: str = matches.group(3)
        sys.path.insert(0, path_to_source_file)

        spec: ModuleSpec = importlib.util.spec_from_file_location(source_file_name, f'{path_to_source_file}/{source_file_name}.{source_file_extension}')
        module: ModuleType = importlib.util.module_from_spec(spec)
        assert isinstance(spec.loader, Loader)  # see https://github.com/python/typeshed/issues/2793
        spec.loader.exec_module(module)

        scope: ModuleType = module
        if matches.group(4):
            class_name: str = matches.group(4)[:-1]
            scope = getattr(scope, class_name)

        method_name: str = matches.group(5)
        func = getattr(scope, method_name)

        if func:
            if inspect.ismethod(func.__call__):
                # func is a non-function class or instance, and we want to inject its __call__ method
                func = func.__call__
            self._func = func

            params = {}
            for name, info in inspect.signature(self._func).parameters.items():
                default = info.default
                if default is inspect.Parameter.empty:
                    # We use MissingArgument as a placeholder for positional parameters that don't have a default
                    # argument.
                    default = MissingArgument
                params[name] = default
            self._params = params


class MissingArgument:
    pass
