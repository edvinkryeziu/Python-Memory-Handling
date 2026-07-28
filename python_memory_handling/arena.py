"""Arena: a big chunk of memory made up of one or more pools."""
from __future__ import annotations

from typing import List

from pool import Pool


class Arena:
    """Top-level memory region. Holds pools, charges their capacity against
    its own budget.
    """

    def __init__(self, capacity_bytes: int = 256 * 1024) -> None:
        self.pools: List[Pool] = []
        self.capacity_bytes: int = capacity_bytes
        self.used_bytes: int = 0

    def has_space_for_pool(self, pool_size: int) -> bool:
        return (self.capacity_bytes - self.used_bytes) >= pool_size

    def remaining_bytes(self) -> int:
        return self.capacity_bytes - self.used_bytes

    def add_pool(self, pool: Pool) -> None:
        """Attach a pool to this arena and reserve its capacity.

        Raises MemoryError if it doesn't fit, ValueError if it's already
        been added.
        """
        if pool in self.pools:
            raise ValueError("pool already added to this arena")

        if not self.has_space_for_pool(pool.capacity_bytes):
            raise MemoryError("arena is full for a new pool")

        self.pools.append(pool)
        self.used_bytes += pool.capacity_bytes

    def stats(self) -> dict:
        return {
            "capacity_bytes": self.capacity_bytes,
            "used_bytes": self.used_bytes,
            "free_bytes": self.remaining_bytes(),
            "pools": len(self.pools),
        }
