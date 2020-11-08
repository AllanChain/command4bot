from typing import Iterable, Optional

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from . import Command, CommandRegistry, FallbackRegistry, Setup, SetupRegistry
from .typing_ext import Decorator, F
from .utils import flex_decorator, split_keyword


class Config(TypedDict):
    text_general_response: str
    text_help_hint: str
    text_possible_command: str
    text_command_closed: str
    command_parameter_blacklist: Iterable[str]
    command_needs_blacklist: Iterable[str]


DEFAULT_CONFIG: Config = {
    "text_general_response": "Get!",
    "text_help_hint": "Help:",
    "text_possible_command": "Possible:",
    "text_command_closed": "CLOSED",
    "command_parameter_blacklist": ("self",),
    "command_needs_blacklist": ("payload",),
}


class CommandsManager:
    def __init__(
        self,
        setup_reg=None,
        command_reg=None,
        fallback_reg=None,
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

    def exec(self, content: str, **kwargs) -> Optional[str]:
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

    @flex_decorator
    def setup(self) -> Decorator:
        def deco(setup_func: F) -> F:
            self.setup_reg.register(Setup(setup_func))
            return setup_func

        return deco

    @flex_decorator
    def fallback(self, priority: int = 10) -> Decorator:
        def deco(fallback_func: F) -> F:
            self.fallback_reg.register(fallback_func, priority)
            return fallback_func

        return deco

    @flex_decorator
    def command(
        self,
        keywords: Iterable[str] = None,
        groups: Iterable[str] = None,
        default_closed: bool = False,
    ) -> Decorator:
        def deco(command_func: F) -> F:
            command = Command(
                command_func,
                keywords or [command_func.__name__],
                groups or [],
                default_closed,
                parameter_blacklist=self.config["command_parameter_blacklist"],
                needs_blacklist=self.config["command_needs_blacklist"],
            )
            self.command_reg.register(command)
            self.setup_reg.check_command(command)
            if self.command_reg.resolve_command_status(command):
                self.setup_reg.update_reference(command)
            return command_func

        return deco

    def close(self, name: str) -> None:
        command_will_close = self.command_reg.get_commands_will_close(name)
        self.command_reg.set_status(name, False)
        for command in command_will_close:
            self.setup_reg.update_reference(command, False)

    def open(self, name: str) -> None:
        command_will_open = self.command_reg.get_commands_will_open(name)
        self.command_reg.set_status(name, True)
        for command in command_will_open:
            self.setup_reg.update_reference(command, True)

    def help_with_similar(self, content: str) -> str:
        "Will be wrapped as fallback in __init__"

        keyword, _ = split_keyword(content)
        # get command not found help message
        helps = self.get_possible_keywords_help(keyword)
        # No similar commands found
        if not helps:
            return "\n".join(
                (
                    self.config["text_general_response"],
                    self.config["text_help_hint"],
                )
            )
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
    ) -> Optional[Iterable[str]]:
        command_matches = self.command_reg.get_similar_commands(keyword)
        if command_matches:
            return (command.brief_help for command in command_matches)
        return None
