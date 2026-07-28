"""MemoryManager: ties arenas, pools and blocks together."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from arena import Arena
from block import Block
from pool import Pool

# a pick-pool function takes the list of arenas and a requested size,
# and returns a pool that can fit it (or None)
PickPoolFn = Callable[[List[Arena], int], Optional[Pool]]


class MemoryManager:
    """Singleton that handles allocate/deallocate across the whole
    arena -> pool -> block hierarchy.

    Only one instance ever exists, so every part of a program sees the
    same set of arenas. Allocation picks (or creates) a pool via the
    current policy, then reuses a free block if one's available.
    """

    _instance: Optional["MemoryManager"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self.arenas: List[Arena] = []
        self._owner: Dict[Block, Pool] = {}

        # first-fit unless someone swaps it out with set_pick_policy
        self._pick_pool: PickPoolFn = self._first_fit

    def set_pick_policy(self, fn: PickPoolFn) -> None:
        self._pick_pool = fn

    def _sizeof(self, value: Any) -> int:
        """Rough, made-up byte cost for a value - not how CPython
        actually sizes things, just enough to make pools fill up at
        different rates depending on what you allocate.
        """
        if isinstance(value, bool):
            return 1
        if isinstance(value, (int, float)):
            return 8
        if isinstance(value, (bytes, bytearray)):
            return len(value)
        if isinstance(value, str):
            return len(value)
        if isinstance(value, (list, tuple, set)):
            return len(value) * 8
        if isinstance(value, dict):
            return len(value) * 16
        return 32

    def _first_fit(self, arenas: List[Arena], size: int) -> Optional[Pool]:
        """First pool that has room for size. None if nothing fits."""
        for arena in arenas:
            for pool in arena.pools:
                if pool.has_space_for(size):
                    return pool
        return None

    def _best_fit(self, arenas: List[Arena], size: int) -> Optional[Pool]:
        """Pool with room for size that has the least space left over."""
        candidates: List[Pool] = []
        for arena in arenas:
            for pool in arena.pools:
                if pool.has_space_for(size):
                    candidates.append(pool)
        if not candidates:
            return None
        return min(candidates, key=lambda p: p.remaining_bytes())

    def _create_pool_in_some_arena(self, min_pool_bytes: int) -> Pool:
        """No existing pool fit, so make a new one - reusing an arena
        that has room, or spinning up a new arena if none do.
        """
        for arena in self.arenas:
            if arena.has_space_for_pool(4096):  # default pool size
                pool = Pool()
                arena.add_pool(pool)
                return pool

        arena = Arena()
        self.arenas.append(arena)
        pool = Pool()
        arena.add_pool(pool)
        return pool

    def allocate(self, value: Any) -> Block:
        size = self._sizeof(value)

        pool = self._pick_pool(self.arenas, size)
        if pool is None:
            pool = self._create_pool_in_some_arena(size)

        # prefer reusing a free block over making a new instance
        reusable = next((b for b in pool.blocks if b.is_free), None)
        if reusable is None:
            block = Block(size_bytes=size)
            block.store(value)
            pool.add_block(block)
            self._owner[block] = pool
            return block

        reusable.size_bytes = size
        pool.add_block(reusable)
        reusable.store(value)
        self._owner[reusable] = pool
        return reusable

    def deallocate(self, block: Block) -> None:
        pool = self._owner.get(block)
        if pool is None:
            raise KeyError("unknown block; cannot deallocate")

        pool.remove_block(block)
        block.clear()

    def stats(self) -> dict:
        pools_count = sum(len(a.pools) for a in self.arenas)
        blocks_total = 0
        blocks_free = 0
        used_bytes_pools = 0

        for arena in self.arenas:
            for pool in arena.pools:
                s = pool.stats()
                blocks_total += s["blocks_total"]
                blocks_free += s["blocks_free"]
                used_bytes_pools += s["used_bytes"]

        return {
            "arenas": len(self.arenas),
            "pools": pools_count,
            "blocks_total": blocks_total,
            "blocks_free": blocks_free,
            "blocks_used": blocks_total - blocks_free,
            "bytes_used_in_pools": used_bytes_pools,
        }


if __name__ == "__main__":
    mm = MemoryManager()
    blk1 = mm.allocate("hello")          # 5 bytes
    blk2 = mm.allocate([1, 2, 3, 4, 5])  # 5 * 8 = 40 bytes
    mm.deallocate(blk1)
    blk3 = mm.allocate("world!")         # should reuse blk1's slot

    print("reused:", blk3 is blk1)
    print("stats:", mm.stats())
