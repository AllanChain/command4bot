from collections import defaultdict
from typing import Callable, List, Optional


class FallbackRegistry:
    _reg: defaultdict
    _sorted: Optional[List[Callable]]

    def __init__(self) -> None:
        self._reg = defaultdict(list)
        self._sorted = None

    def register(self, fallback_func: Callable, priority: int) -> None:
        if self._sorted is not None:
            raise ValueError(
                "Cannot append fallback functions to registry"
                "because FallbackRegistry is frozen"
            )
        self._reg[priority].append(fallback_func)

    def all(self) -> List[Callable]:
        if self._sorted is None:
            self._sorted = list(
                func
                for funcs in sorted(
                    self._reg.values(), key=lambda x: x[0], reverse=True
                )
                for func in funcs
            )
        return self._sorted
