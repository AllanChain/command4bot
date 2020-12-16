from typing import Any, Iterable, List, Optional, Tuple, Union, overload

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from .command import BaseCommandRegistry, Command, CommandRegistry
from .context import Context, ContextRegistry
from .fallback import FallbackRegistry
from .typing_ext import Decorator, F


def split_keyword(content: str) -> Tuple[str, str]:
    """Split content into command name an payload

    :param content: text input to split
    :type content: str
    :return: (command name, payload)
    :rtype: Tuple[str, str]
    """
    split_st = content.split(" ", 1)
    return (split_st[0], split_st[1] if len(split_st) == 2 else "")


class Config(TypedDict):
    """Config dict for :class:`ComamndsManager`"""

    enable_default_fallback: bool
    """Whether to enable default fallback handler.

    The default fallback handler returns similar command help
    or a general response"""
    text_general_response: str
    """For default fallback handler :meth:`Command4bot.help_with_similar`.

    Default to ``"Copy! But the bot can't understand it."``

    What to return if neither exact nor similar command handlers found
    for the input"""
    text_possible_command: str
    """For default fallback handler :meth:`Command4bot.help_with_similar`.

    Default to ``"Did you misspell it? Possible commands are:"``

    What to say before a list of command helps if only similar command
    handlers foundfor the input"""
    text_command_closed: str
    """What to return if target command handler is closed.

    Default to ``"Sorry, this command is currently disabled."``"""
    command_parameter_ignore: Iterable[str]
    """Ignore these parameters of command handlers when constructing keyword
    arguments to pass

    Default to ``("self",)``. The manager will never try to pass these
    parameters to the handler"""
    command_context_ignore: Iterable[str]
    """Do not regard these parameters of command handlers as context names
    (a.k.a dependencies)


    Default to ``()``. These parameters are to receive extra context
    passed to :meth:`CommandsManager.exec`"""
    command_payload_parameter: str
    """The payload parameter name of command handlers

    Default to ``"payload"``"""


DEFAULT_CONFIG = Config(
    enable_default_fallback=True,
    text_general_response="Copy! But the bot can't understand it.",
    text_possible_command="Did you misspell it? Possible commands are:",
    text_command_closed="Sorry, this command is currently disabled.",
    command_parameter_ignore=("self",),
    command_context_ignore=(),
    command_payload_parameter="payload",
)


class CommandsManager:
    context_reg: ContextRegistry
    command_reg: BaseCommandRegistry
    fallback_reg: FallbackRegistry
    config: Config

    def __init__(
        self,
        context_reg: ContextRegistry = None,
        command_reg: BaseCommandRegistry = None,
        fallback_reg: FallbackRegistry = None,
        config: Optional[Config] = None,
        **kwargs,
    ):
        self.context_reg = context_reg or ContextRegistry()
        self.command_reg = command_reg or CommandRegistry()
        self.fallback_reg = fallback_reg or FallbackRegistry()

        self.config: Config = DEFAULT_CONFIG.copy()
        self.config.update(kwargs)  # type: ignore
        if config:
            # python/mypy#9335
            self.config.update(config)  # type: ignore
        if self.config["enable_default_fallback"]:
            self.fallback_reg.register(self.help_with_similar, priority=-1)

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
                    context_name: self.context_reg.get(context_name).value
                    for context_name in command.contexts
                }
            )
            return command(payload=payload, **func_args)

        for fallback_func in self.fallback_reg.all():
            result = fallback_func(content)
            if result is not None:
                return result
        return None

    @overload
    def context(self, context_func: F) -> F:
        ...

    @overload
    def context(
        self, context_func: None = ..., *, enable_cache: bool = ...
    ) -> Decorator:
        ...

    def context(
        self, context_func: Optional[F] = None, *, enable_cache: bool = True
    ) -> Union[F, Decorator]:
        """Decorator to register a context (a.k.a. command dependency).

        This decorator can be used with or without parentheses.
        """

        def deco(context_func: F) -> F:
            self.context_reg.register(
                Context(context_func, enable_cache=enable_cache)
            )
            return context_func

        if context_func:
            return deco(context_func)
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
                context_ignore=self.config["command_context_ignore"],
                payload_parameter=self.config["command_payload_parameter"],
            )
            self.command_reg.register(command)
            self.context_reg.check_command(command)
            if self.command_reg.resolve_command_status(command):
                self.context_reg.update_reference(command)
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
            self.context_reg.update_reference(command, False)

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
            self.context_reg.update_reference(command, True)

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
                self.config["text_possible_command"],
                *helps,
            )
        )

    def get_possible_keywords_help(self, keyword: str) -> List[str]:
        """Get the help of keywords similar to ``keyword``.

        Used by ``help_with_similar``.

        :param keyword: The misspelled keyword to find similar keywrod for.
        :type keyword: str
        :return: Brief help string of the similar commands.
        :rtype: List[str]
        """
        return [
            command.brief_help
            for command in self.command_reg.get_similar_commands(keyword)
        ]
