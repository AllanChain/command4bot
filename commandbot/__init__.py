from inspect import signature, isgenerator
from difflib import get_close_matches
from textwrap import dedent
from collections import defaultdict

from typing import Callable


TEXT_GENERAL_RESPONSE = 'Get!'
TEXT_HELP_HINT = 'Help:'
TEXT_POSSIBLE_COMMAND = 'Possible:'
TEXT_COMMAND_CLOSED = 'CLOSED'


def split_keyword(content):
    split_st = content.split(' ', 1)
    if len(split_st) == 1:
        return split_st[0], ''
    return split_st


def flex_decorator(deco):
    def flex_deco(self, *args, **kargs):
        # called as decorator
        if not kargs and len(args) == 1 and callable(args[0]):
            return deco(self)(args[0])
        # else as a decorator factory
        return deco(self, *args, **kargs)

    return flex_deco


class FallbackRegistry:
    def __init__(self):
        self._reg = defaultdict(list)
        self._sorted = None

    def register(self, fallback_func, priority):
        if self._sorted is not None:
            raise ValueError(
                'Cannot append fallback functions to registry'
                'because FallbackRegistry is frozen'
            )
        self._reg[priority].append(fallback_func)

    def __iter__(self):
        if self._sorted is None:
            self._sorted = list(
                func
                for funcs in sorted(
                    self._reg.values(), key=lambda x: x[0], reverse=True
                )
                for func in funcs
            )
        return iter(self._sorted)


class Command:
    def __init__(
        self,
        command_func,
        keywords,
        groups,
        parameter_blacklist=('self',),
        needs_blacklist=('payload',),
    ):
        self.command_func = command_func
        self.name = command_func.__name__
        self.keywords = keywords
        self.groups = groups
        self.parameters = []
        self.needs = []

        if self.__doc__ is None:
            self.help = (
                '/'.join(self.keywords) + ' ' + command_func.__name__
            )
        else:
            self.help = dedent(command_func.__doc__).strip()
        self.brief_help = '- ' + self.help.split('\n', 1)[0]

        for parameter in signature(command_func).parameters:
            if parameter not in parameter_blacklist:
                self.parameters.append(parameter)
                if parameter not in needs_blacklist:
                    self.needs.append(parameter)

    def __call__(self, payload, **kargs):
        return self.command_func(
            payload,
            **{k: v for k, v in kargs.items() if k in self.parameters},
        )


class BaseCommandRegistry:
    def __init__(self):
        self._reg = {}

    def register(self, command: Command):
        for keyword in command.keywords:
            self._reg[keyword] = command

    def get(self, keyword):
        return self._reg.get(keyword)

    def get_similar_commands(self, keyword):
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
    def __init__(self):
        super().__init__()
        self._status = {}

    def get_status(self, name: str):
        return self._status.get(name, True)

    def set_status(self, name: str, status: bool):
        self._status[name] = status

    def resolve_command_status(self, command):
        if not self.get_status(command.name):
            return False
        return all(
            self.get_status(group_name) for group_name in command.groups
        )


class SetupRegistry:
    def __init__(self):
        self._reg = {}

    def register(self, setup):
        if setup.name in self._reg:
            raise ValueError('Command name duplicate')

        self._reg[setup.name] = setup

    def get(self, setup_name):
        return self._reg[setup_name]

    def check_command(self, command):
        for needed in command.needs:
            if needed not in self._reg:
                raise ValueError(f'Unrecognized parameter "{needed}"')

    def update_reference(self, command, increase=True):
        for needed in command.needs:
            self._reg[needed].reference_count += 1 if increase else -1


class Setup:
    def __init__(self, setup_func: Callable, enable_cache=True):
        self.is_cached = False
        self.cached_value = None
        self.cached_generator = None
        self.reference_count = 0
        self.enable_cache = enable_cache
        self.setup_func = setup_func
        self.name = setup_func.__name__

    @property
    def value(self):
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

    def cleanup(self):
        if self.is_cached:
            if self.cached_generator is not None:
                try:
                    next(self.cached_generator)
                except StopIteration:
                    pass
                self.cached_generator = None
            self.cached_value = None
            self.is_cached = False


class CommandsManager:
    def __init__(
        self,
        setup_reg=None,
        command_reg=None,
        fallback_reg=None,
        command_parameter_blacklist: tuple = ('self',),
        command_needs_blacklist: tuple = ('payload',),
    ):
        self.setup_reg = setup_reg or SetupRegistry()
        self.command_reg = command_reg or CommandRegistry()
        self.fallback_reg = fallback_reg or FallbackRegistry()
        self.fallback_reg.register(self.help_with_similar, priority=-1)

        self.command_parameter_blacklist = command_parameter_blacklist
        self.command_needs_blacklist = command_needs_blacklist

    def exec(self, content, **kargs):
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

        for fallback_func in self.fallback_reg:
            result = fallback_func(content)
            if result is not None:
                return result

    @flex_decorator
    def setup(self, priority=10):
        def deco(setup_func):
            self.setup_reg.register(Setup(setup_func, priority))
            return setup_func

        return deco

    @flex_decorator
    def fallback(self, priority=10):
        def deco(fallback_func):
            self.fallback_reg.register(fallback_func, priority)
            return fallback_func

        return deco

    @flex_decorator
    def command(self, keywords=None, groups=None):
        def deco(command_func):
            command = Command(
                command_func,
                keywords or [command_func.__name__],
                groups or [],
                parameter_blacklist=self.command_parameter_blacklist,
                needs_blacklist=self.command_needs_blacklist,
            )
            self.command_reg.register(command)
            self.setup_reg.check_command(command)
            if self.command_reg.resolve_command_status(command):
                self.setup_reg.update_reference(command)
            return command_func

        return deco

    def help_with_similar(self, content):
        'Will be wrapped as fallback in __init__'

        keyword, _ = split_keyword(content)
        # get command not found help message
        helps = self.get_possible_keywords_help(keyword)
        # No similar commands found
        if not helps:
            return '\n'.join((TEXT_GENERAL_RESPONSE, TEXT_HELP_HINT))
        # print similar commands
        return '\n'.join(
            (TEXT_GENERAL_RESPONSE, TEXT_POSSIBLE_COMMAND, *helps)
        )

    def get_possible_keywords_help(self, keyword):
        command_matches = self.command_reg.get_similar_commands(keyword)
        if command_matches:
            return (command.brief_help for command in command_matches)
