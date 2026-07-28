"""Block: the smallest allocatable unit in the simulator."""
from __future__ import annotations

from typing import Any


class Block:
    """A single slot that can hold one value.

    Blocks start out free. Once something is stored in them they're
    marked used, and they go back to free (and their value is dropped)
    when they're cleared.
    """

    def __init__(self, size_bytes: int = 0) -> None:
        self._memory_unit: Any = None
        self.is_free: bool = True
        self.size_bytes: int = size_bytes

    def store(self, value: Any) -> None:
        self._memory_unit = value
        self.is_free = False

    def retrieve(self) -> Any:
        return self._memory_unit

    def clear(self) -> None:
        """Drop the stored value and mark the block free again."""
        self._memory_unit = None
        self.is_free = True

    def __repr__(self) -> str:
        state = "free" if self.is_free else "used"
        return f"<Block {state} size={self.size_bytes}>"
