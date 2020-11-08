from typing import Callable, List, Union

from .typing_ext import F


def split_keyword(content: str) -> List[str]:
    split_st = content.split(" ", 1)
    if len(split_st) == 1:
        return [split_st[0], ""]
    return split_st


def flex_decorator(
    deco_factory: Callable[..., Callable[[F], F]]
) -> Union[Callable[..., Callable[[F], F]], Callable[[F], F]]:
    def flex_deco(self, *args, **kwargs) -> Union[Callable[[F], F], F]:
        # called as decorator
        if not kwargs and len(args) == 1 and callable(args[0]):
            return deco_factory(self)(args[0])
        # else as a decorator factory
        return deco_factory(self, *args, **kwargs)

    return flex_deco
