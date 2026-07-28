"""Pool: a fixed-size group of blocks, owned by an arena."""
from __future__ import annotations

from typing import List, Optional

from block import Block


class Pool:
    """Holds a bunch of blocks and keeps track of how much space is used.

    Blocks aren't thrown away once they're freed - they stay in the pool
    so allocate() can hand them back out instead of making new ones.
    """

    def __init__(self, capacity_bytes: int = 4096) -> None:
        self.blocks: List[Block] = []
        self.capacity_bytes: int = capacity_bytes
        self.used_bytes: int = 0

    def has_space_for(self, size: int) -> bool:
        return (self.capacity_bytes - self.used_bytes) >= size

    def remaining_bytes(self) -> int:
        return self.capacity_bytes - self.used_bytes

    def _find_reusable_block(self) -> Optional[Block]:
        for blk in self.blocks:
            if blk.is_free:
                return blk
        return None

    def add_block(self, block: Block) -> None:
        """Register a block as allocated in this pool.

        Works both for a brand-new block and for reusing one that was
        already in self.blocks but marked free. Raises MemoryError if
        there isn't room, or ValueError if the block is already in use.
        """
        if block in self.blocks and not block.is_free:
            raise ValueError("block already in pool and allocated")

        if not self.has_space_for(block.size_bytes):
            raise MemoryError("pool is full for a new block")

        if block not in self.blocks:
            self.blocks.append(block)

        self.used_bytes += block.size_bytes

    def remove_block(self, block: Block) -> None:
        """Free up the space used by block, but keep it around for reuse."""
        if block not in self.blocks:
            raise ValueError("block not in pool")

        self.used_bytes -= block.size_bytes

    def stats(self) -> dict:
        total = len(self.blocks)
        free = sum(1 for blk in self.blocks if blk.is_free)
        return {
            "capacity_bytes": self.capacity_bytes,
            "used_bytes": self.used_bytes,
            "free_bytes": self.remaining_bytes(),
            "blocks_total": total,
            "blocks_free": free,
            "blocks_used": total - free,
        }
