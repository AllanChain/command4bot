from inspect import isgenerator
from typing import Any, Dict

from .command import Command
from .typing_ext import F


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

    def register(self, setup: Setup) -> None:
        if setup.name in self._reg:
            raise ValueError(f'Setup name "{setup.name}" duplicate')

        self._reg[setup.name] = setup

    def get(self, setup_name: str) -> Setup:
        return self._reg[setup_name]

    def check_command(self, command: Command) -> None:
        for needed in command.needs:
            if needed not in self._reg:
                raise ValueError(f'Unrecognized setup name: "{needed}"')

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
