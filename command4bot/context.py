import threading
from inspect import isgenerator
from typing import Any, Callable, Dict, Generator, Optional

from .command import Command
from .typing_ext import F


class Context:
    name: str
    context_func: Callable
    enable_cache: bool
    is_cached: bool
    cached_value: Any
    cached_generator: Optional[Generator]
    reference_count: int

    def __init__(self, context_func: F, enable_cache: bool = True) -> None:
        self.name = context_func.__name__
        # python/mypy#2427
        self.context_func = context_func  # type: ignore
        self.enable_cache = enable_cache

        self.is_cached = False
        self.cached_value = None
        self.cached_generator = None
        self.reference_count = 0
        self.__lock = threading.Lock()

    @property
    def value(self) -> Any:
        with self.__lock:
            if self.is_cached:
                return self.cached_value

            result = self.context_func()

            if isgenerator(result):
                if self.enable_cache:
                    self.cached_generator = result
                result = next(result)

            if self.enable_cache:
                self.is_cached = True
                self.cached_value = result

            return result

    def cleanup(self) -> None:
        with self.__lock:
            if self.is_cached:
                if self.cached_generator is not None:
                    try:
                        next(self.cached_generator)
                    except StopIteration:
                        pass
                    self.cached_generator = None
                self.cached_value = None
                self.is_cached = False


class ContextRegistry:
    _reg: Dict[str, Context]

    def __init__(self):
        self._reg = {}

    def register(self, context: Context) -> None:
        if context.name in self._reg:
            raise ValueError(f'Context name "{context.name}" duplicate')

        self._reg[context.name] = context

    def get(self, context_name: str) -> Context:
        return self._reg[context_name]

    def check_command(self, command: Command) -> None:
        for context_name in command.contexts:
            if context_name not in self._reg:
                raise ValueError(
                    f'Unrecognized context name: "{context_name}"'
                )

    def update_reference(self, command: Command, increase: bool = True):
        for context_name in command.contexts:
            context = self._reg[context_name]
            context.reference_count += 1 if increase else -1
            if context.reference_count == 0:
                context.cleanup()
            elif context.reference_count < 0:  # pragma: no cover
                raise ValueError(
                    "Context reference less than zero. "
                    "Are you using your own command registry class?"
                )
