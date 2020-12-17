from collections import defaultdict
from difflib import get_close_matches
from inspect import signature
from textwrap import dedent
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    overload,
)


def calc_status_diff(
    before: Dict[str, bool], after: Dict[str, bool]
) -> Dict[str, bool]:
    return {
        k: v
        for k, v in set(after.items()) - set(before.items())
        if k in before or not v  # Same name different state or closed
    }


class Command:
    name: str
    keywords: Iterable[str]
    groups: Iterable[str]
    contexts: Iterable[str]
    parameters: Iterable[str]

    def __init__(
        self,
        command_func: Callable,
        keywords: Iterable[str],
        groups: Iterable[str],
        parameter_ignore: Iterable[str],
        context_ignore: Iterable[str],
        payload_parameter: str,
    ) -> None:
        self.command_func = command_func
        self.name = command_func.__name__
        self.keywords = keywords
        self.groups = groups
        self.parameters = []
        self.contexts = []

        if command_func.__doc__ is None:
            self.help = "/".join(self.keywords) + " " + command_func.__name__
        else:
            self.help = dedent(command_func.__doc__).strip()
        self.brief_help = "- " + self.help.split("\n", 1)[0]

        context_ignore = [*context_ignore, payload_parameter]

        for parameter in signature(command_func).parameters:
            if parameter not in parameter_ignore:
                self.parameters.append(parameter)
                if parameter not in context_ignore:
                    self.contexts.append(parameter)

    def __call__(self, **kwargs: Any) -> Any:
        return self.command_func(
            **{k: v for k, v in kwargs.items() if k in self.parameters},
        )


class BaseCommandRegistry:
    _reg: Dict[str, Command]
    _groups: defaultdict

    def __init__(self):
        self._reg = {}
        self._groups = defaultdict(list)

    def register(self, command: Command) -> None:
        for keyword in command.keywords:
            if keyword in self._reg:
                raise ValueError(f'Duplicated command keyword: "{keyword}"')
            self._reg[keyword] = command

        if command.name in self._groups or command.name in command.groups:
            raise ValueError(f'Duplicated command name: "{command.name}"')
        self._groups[command.name] = [command]

        for group_name in command.groups:
            # No need to check duplication here!
            self._groups[group_name].append(command)

    def get(self, keyword: str) -> Optional[Command]:
        return self._reg.get(keyword)

    def get_similar_commands(self, keyword: str) -> List[Command]:
        return [
            self._reg[match]
            for match in get_close_matches(keyword, self._reg.keys())
            if self.resolve_command_status(self._reg[match])
        ]

    def get_status(self, name: str) -> bool:
        raise NotImplementedError

    def set_status(self, name: str, status: bool) -> None:
        raise NotImplementedError

    def set_default_closed(self, name: str) -> None:
        raise NotImplementedError

    @overload
    def mark_default_closed(self, *args: Callable) -> Callable:
        ...

    @overload
    def mark_default_closed(self, *args: str) -> None:
        ...

    def mark_default_closed(
        self, *args: Union[str, Callable]
    ) -> Optional[Callable]:
        for arg in args:
            name = arg.__name__ if callable(arg) else arg
            if self.get(name):
                raise ValueError(
                    f"Cannot mark {name} as default closed because "
                    "the command already registered"
                )
            self.set_default_closed(name)
        if args and callable(args[0]):
            return args[0]
        return None

    def resolve_command_status(self, command: Command) -> bool:
        if not self.get_status(command.name):
            return False
        return all(
            self.get_status(group_name) for group_name in command.groups
        )

    def open(self, name: str) -> Iterable[Command]:
        commands_opened = [
            command
            for command in self._groups[name]
            if all(
                self.get_status(group_name)
                for group_name in [command.name, *command.groups]
                if group_name != name
            )
        ]
        self.set_status(name, True)
        return commands_opened

    def close(self, name: str) -> Iterable[Command]:
        commands_closed = [
            command
            for command in self._groups[name]
            if self.resolve_command_status(command)
        ]
        self.set_status(name, False)
        return commands_closed

    def batch_update_status(
        self, status_diff: Dict[str, bool]
    ) -> Tuple[List[Command], List[Command]]:
        to_close = [k for k, v in status_diff.items() if not v]
        to_open = [k for k, v in status_diff.items() if v]
        commands_closed: List[Command] = []
        commands_opened: List[Command] = []
        for name in to_close:
            commands_closed.extend(self.close(name))
        for name in to_open:
            commands_opened.extend(self.open(name))
        return commands_closed, commands_opened


class CommandRegistry(BaseCommandRegistry):
    def __init__(self):
        super().__init__()
        self._status = {}

    def get_status(self, name: str) -> bool:
        return self._status.get(name, True)

    def set_status(self, name: str, status: bool) -> None:
        self._status[name] = status

    def set_default_closed(self, name: str) -> None:
        self._status[name] = False

    def calc_status_diff(self, new_status: Dict[str, bool]) -> Dict[str, bool]:
        return calc_status_diff(self._status, new_status)
