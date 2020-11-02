from collections import defaultdict
from difflib import get_close_matches
from inspect import isgenerator, signature
from textwrap import dedent
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    TypeVar,
    Union,
)

Function = Callable[..., Any]
F = TypeVar("F", bound=Function)
Decorator = Callable[[F], F]

TEXT_GENERAL_RESPONSE = "Get!"
TEXT_HELP_HINT = "Help:"
TEXT_POSSIBLE_COMMAND = "Possible:"
TEXT_COMMAND_CLOSED = "CLOSED"


def split_keyword(content):
    split_st = content.split(" ", 1)
    if len(split_st) == 1:
        return split_st[0], ""
    return split_st


def flex_decorator(
    deco_factory: Callable[..., Callable[[F], F]]
) -> Union[Callable[..., Callable[[F], F]], Callable[[F], F]]:
    def flex_deco(self, *args, **kargs) -> Union[Callable[[F], F], F]:
        # called as decorator
        if not kargs and len(args) == 1 and callable(args[0]):
            return deco_factory(self)(args[0])
        # else as a decorator factory
        return deco_factory(self, *args, **kargs)

    return flex_deco


class FallbackRegistry:
    _reg: defaultdict
    _sorted: Optional[List[Function]]

    def __init__(self) -> None:
        self._reg = defaultdict(list)
        self._sorted = None

    def register(self, fallback_func: F, priority: int) -> None:
        if self._sorted is not None:
            raise ValueError(
                "Cannot append fallback functions to registry"
                "because FallbackRegistry is frozen"
            )
        self._reg[priority].append(fallback_func)

    def all(self) -> List[Function]:
        if self._sorted is None:
            self._sorted = list(
                func
                for funcs in sorted(
                    self._reg.values(), key=lambda x: x[0], reverse=True
                )
                for func in funcs
            )
        return self._sorted


class Command:
    name: str
    keywords: Iterable[str]
    groups: Iterable[str]
    needs: Iterable[str]
    parameters: Iterable[str]

    def __init__(
        self,
        command_func: Function,
        keywords: Iterable[str],
        groups: Iterable[str],
        default_closed: bool,
        parameter_blacklist: Iterable[str] = ("self",),
        needs_blacklist: Iterable[str] = ("payload",),
    ) -> None:
        self.command_func = command_func
        self.name = command_func.__name__
        self.keywords = keywords
        self.groups = groups
        self.default_closed = default_closed
        self.parameters = []
        self.needs = []

        if command_func.__doc__ is None:
            self.help = "/".join(self.keywords) + " " + command_func.__name__
        else:
            self.help = dedent(command_func.__doc__).strip()
        self.brief_help = "- " + self.help.split("\n", 1)[0]

        for parameter in signature(command_func).parameters:
            if parameter not in parameter_blacklist:
                self.parameters.append(parameter)
                if parameter not in needs_blacklist:
                    self.needs.append(parameter)

    def __call__(self, payload: str, **kargs: Any) -> Any:
        return self.command_func(
            payload,
            **{k: v for k, v in kargs.items() if k in self.parameters},
        )


class BaseCommandRegistry:
    _reg: Dict[str, Command]

    def __init__(self):
        self._reg = {}

    def register(self, command: Command):
        for keyword in command.keywords:
            self._reg[keyword] = command

    def get(self, keyword: str):
        return self._reg.get(keyword)

    def get_similar_commands(self, keyword: str):
        return (
            self._reg[match]
            for match in get_close_matches(keyword, self._reg.keys())
            if self.resolve_command_status(self._reg[match])
        )

    def get_status(self, name: str):
        raise NotImplementedError

    def set_status(self, name: str, status: bool):
        raise NotImplementedError

    def resolve_command_status(self, command: Command):
        raise NotImplementedError


class CommandRegistry(BaseCommandRegistry):
    _groups: defaultdict

    def __init__(self):
        super().__init__()
        self._status = {}
        self._groups = defaultdict(list)

    def register(self, command: Command) -> None:
        super().register(command)

        self._groups[command.name] = [command]
        for group_name in command.groups:
            self._groups[group_name].append(command)

        if command.default_closed:
            self.set_status(command.name, False)

    def get_status(self, name: str) -> bool:
        return self._status.get(name, True)

    def set_status(self, name: str, status: bool) -> None:
        self._status[name] = status

    def resolve_command_status(self, command: Command) -> bool:
        if not self.get_status(command.name):
            return False
        return all(
            self.get_status(group_name) for group_name in command.groups
        )

    def get_commands_will_open(self, name: str) -> Iterable[Command]:
        return [
            command
            for command in self._groups[name]
            if all(
                self.get_status(group_name)
                for group_name in [command.name, *command.groups]
                if group_name != name
            )
        ]

    def get_commands_will_close(self, name: str) -> Iterable[Command]:
        return [
            command
            for command in self._groups[name]
            if self.resolve_command_status(command)
        ]


class Setup:
    def __init__(self, setup_func: F, enable_cache: bool = True) -> None:
        self.is_cached = False
        self.cached_value = None
        self.cached_generator = None
        self.reference_count = 0
        self.enable_cache = enable_cache
        self.setup_func = setup_func
        self.name = setup_func.__name__

    @property
    def value(self) -> Any:
        if self.is_cached:
            return self.cached_value

        result = self.setup_func()

        if isgenerator(result):
            self.cached_generator = result
            result = next(result)

        if self.enable_cache:
            self.is_cached = True
            self.cached_value = result

        return result

    def cleanup(self) -> None:
        if self.is_cached:
            if self.cached_generator is not None:
                try:
                    next(self.cached_generator)
                except StopIteration:
                    pass
                self.cached_generator = None
            self.cached_value = None
            self.is_cached = False


class SetupRegistry:
    _reg: Dict[str, Setup]

    def __init__(self):
        self._reg = {}

    def register(self, setup: Setup):
        if setup.name in self._reg:
            raise ValueError("Command name duplicate")

        self._reg[setup.name] = setup

    def get(self, setup_name: str) -> Setup:
        return self._reg[setup_name]

    def check_command(self, command: Command) -> None:
        for needed in command.needs:
            if needed not in self._reg:
                raise ValueError(f'Unrecognized parameter "{needed}"')

    def update_reference(self, command: Command, increase: bool = True):
        for needed in command.needs:
            setup = self._reg[needed]
            setup.reference_count += 1 if increase else -1
            if setup.reference_count == 0:
                setup.cleanup()
            elif setup.reference_count < 0:
                raise ValueError(
                    "Setup reference less than zero." "Race condition?"
                )


class CommandsManager:
    def __init__(
        self,
        setup_reg=None,
        command_reg=None,
        fallback_reg=None,
        command_parameter_blacklist: Iterable[str] = ("self",),
        command_needs_blacklist: Iterable[str] = ("payload",),
    ):
        self.setup_reg = setup_reg or SetupRegistry()
        self.command_reg = command_reg or CommandRegistry()
        self.fallback_reg = fallback_reg or FallbackRegistry()
        self.fallback_reg.register(self.help_with_similar, priority=-1)

        self.command_parameter_blacklist = command_parameter_blacklist
        self.command_needs_blacklist = command_needs_blacklist

    def exec(self, content: str, **kargs) -> Optional[str]:
        keyword, payload = split_keyword(content)
        command = self.command_reg.get(keyword)
        if command is not None:
            # checking if command is closed
            if not self.command_reg.resolve_command_status(command):
                return TEXT_COMMAND_CLOSED
            # finnally call it
            func_args = kargs.copy()
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
                parameter_blacklist=self.command_parameter_blacklist,
                needs_blacklist=self.command_needs_blacklist,
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
            return "\n".join((TEXT_GENERAL_RESPONSE, TEXT_HELP_HINT))
        # print similar commands
        return "\n".join(
            (TEXT_GENERAL_RESPONSE, TEXT_POSSIBLE_COMMAND, *helps)
        )

    def get_possible_keywords_help(
        self, keyword: str
    ) -> Optional[Iterable[str]]:
        command_matches = self.command_reg.get_similar_commands(keyword)
        if command_matches:
            return (command.brief_help for command in command_matches)
        return None
