from typing import Any, Iterable, List, Optional, Union, overload

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from .command import Command, CommandRegistry
from .fallback import FallbackRegistry
from .setup import Setup, SetupRegistry
from .typing_ext import Decorator, F
from .utils import split_keyword


class Config(TypedDict):
    text_general_response: str
    text_possible_command: str
    text_command_closed: str
    command_parameter_ignore: Iterable[str]
    command_needs_ignore: Iterable[str]
    command_payload_parameter: str


DEFAULT_CONFIG = Config(
    text_general_response="Get!",
    text_possible_command="Possible:",
    text_command_closed="CLOSED",
    command_parameter_ignore=("self",),
    command_needs_ignore=(),
    command_payload_parameter="payload",
)


class CommandsManager:
    def __init__(
        self,
        setup_reg: SetupRegistry=None,
        command_reg: CommandRegistry=None,
        fallback_reg: FallbackRegistry=None,
        config: Optional[Config] = None,
        **kwargs,
    ):
        self.setup_reg = setup_reg or SetupRegistry()
        self.command_reg = command_reg or CommandRegistry()
        self.fallback_reg = fallback_reg or FallbackRegistry()
        self.fallback_reg.register(self.help_with_similar, priority=-1)

        self.config: Config = DEFAULT_CONFIG.copy()
        self.config.update(kwargs)  # type: ignore
        if config:
            # python/mypy#9335
            self.config.update(config)  # type: ignore

    def exec(self, content: str, **kwargs) -> Any:
        """Execute given text input ``content``

        :param content: content to execute
        :type content: str
        :return: execution result
        :rtype: Any
        """
        keyword, payload = split_keyword(content)
        command = self.command_reg.get(keyword)
        if command is not None:
            # checking if command is closed
            if not self.command_reg.resolve_command_status(command):
                return self.config["text_command_closed"]
            # finnally call it
            func_args = kwargs.copy()
            func_args.update(
                {
                    needed: self.setup_reg.get(needed).value
                    for needed in command.needs
                }
            )
            return command(payload=payload, **func_args)

        for fallback_func in self.fallback_reg.all():
            result = fallback_func(content)
            if result is not None:
                return result
        return None

    @overload
    def setup(self, setup_func: F) -> F:
        ...

    @overload
    def setup(self, setup_func: None = ...) -> Decorator:
        ...

    def setup(self, setup_func: Optional[F] = None) -> Union[F, Decorator]:
        """Decorator to register a setup (a.k.a. ommand dependency).

        This decorator can be used with or without parentheses.
        """

        def deco(setup_func: F) -> F:
            self.setup_reg.register(Setup(setup_func))
            return setup_func

        if setup_func:
            return deco(setup_func)
        return deco

    @overload
    def fallback(self, fallback_func: F) -> F:
        ...

    @overload
    def fallback(
        self, fallback_func: None = ..., *, priority: int = ...
    ) -> Decorator:
        ...

    def fallback(
        self, fallback_func: Optional[F] = None, *, priority: int = 10
    ) -> Decorator:
        """Decorator to register a fallback handler.

        The fallback handlers registered are called in order of priority,
        with the original text input (``payload``)
        and all other keyword parameters passed to `CommandsManager.exec`,
        until the handler returns something other than ``None``,
        when there is no command found to handle the input.

        :param priority:
            Fallback handlers with higher priority will be called first,
            defaults to 10
        :type priority: int, optional
        """

        def deco(fallback_func: F) -> F:
            self.fallback_reg.register(fallback_func, priority)
            return fallback_func

        if fallback_func:
            return deco(fallback_func)
        return deco

    @overload
    def command(self, command_func: F) -> F:
        ...

    @overload
    def command(
        self,
        command_func: None = ...,
        *,
        keywords: Iterable[str] = ...,
        groups: Iterable[str] = ...,
    ) -> Decorator:
        ...

    def command(
        self,
        command_func: Optional[F] = None,
        *,
        keywords: Iterable[str] = None,
        groups: Iterable[str] = None,
    ) -> Decorator:
        """Decorator to register a command handler.

        The command handler is called
        with the rest of the input (that is, without keyword it self),
        and optional keywords passed to ``CommandsManager.exec``,
        when input matches its keywords.

        The first non-empty line of the function's docstring
        will be used as brief help string of the command.
        And the whole docstring will be used as full help string.

        :param keywords:
            Keywords for command. A keyword is a leading word of text input,
            separated with the rest part by a space.
            Defaults to the name of the comamnd function
        :type keywords: Iterable[str], optional
        :param groups: Group names of the command, defaults to ``[]``
        :type groups: Iterable[str], optional
        """

        def deco(command_func: F) -> F:
            command = Command(
                command_func,
                keywords or [command_func.__name__],
                groups or [],
                parameter_ignore=self.config["command_parameter_ignore"],
                needs_ignore=self.config["command_needs_ignore"],
                payload_parameter=self.config["command_payload_parameter"],
            )
            self.command_reg.register(command)
            self.setup_reg.check_command(command)
            if self.command_reg.resolve_command_status(command):
                self.setup_reg.update_reference(command)
            return command_func

        if command_func:
            return deco(command_func)
        return deco

    def close(self, name: str) -> None:
        """Mark a command or group as closed.

        :param name: The name of the command or group to close.
        :type name: str
        """
        if not self.command_reg.get_status(name):
            return
        command_will_close = self.command_reg.get_commands_will_close(name)
        self.command_reg.set_status(name, False)
        for command in command_will_close:
            self.setup_reg.update_reference(command, False)

    def open(self, name: str) -> None:
        """Mark a command or group as open.

        :param name: The name of the command or group to open.
        :type name: str
        """
        if self.command_reg.get_status(name):
            return
        command_will_open = self.command_reg.get_commands_will_open(name)
        self.command_reg.set_status(name, True)
        for command in command_will_open:
            self.setup_reg.update_reference(command, True)

    def help_with_similar(self, content: str) -> str:
        """Return helps with similar commands hint.

        This is the default fallback handler
        and will be registered in ``__init__``.

        :param content: The text input
        :type content: str
        :return: Help message
        :rtype: str
        """

        keyword, _ = split_keyword(content)
        # get command not found help message
        helps = self.get_possible_keywords_help(keyword)
        # No similar commands found
        if not helps:
            return self.config["text_general_response"]
        # print similar commands
        return "\n".join(
            (
                self.config["text_general_response"],
                self.config["text_possible_command"],
                *helps,
            )
        )

    def get_possible_keywords_help(
        self, keyword: str
    ) -> List[str]:
        """Get the help of keywords similar to ``keyword``.

        Used by ``help_with_similar``.

        :param keyword: The misspelled keyword to find similar keywrod for.
        :type keyword: str
        :return: Brief help string of the similar commands.
        :rtype: List[str]
        """
        return [command.brief_help for command in self.command_reg.get_similar_commands(keyword)]
