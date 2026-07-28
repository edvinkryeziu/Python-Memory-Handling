"""Tests for the arena/pool/block memory simulator."""
from __future__ import annotations

import unittest

from arena import Arena
from block import Block
from memory_manager import MemoryManager


class MemorySimulatorTests(unittest.TestCase):

    def setUp(self) -> None:
        # MemoryManager is a singleton, so reset its state between tests
        self.mm = MemoryManager()
        self.mm.arenas.clear()

    def test_pool_rollover_creates_second_pool(self) -> None:
        self.mm.arenas.append(Arena(capacity_bytes=8192))

        # "aa" costs 2 bytes each, so 3000 of them should overflow a
        # single 4096-byte pool
        for _ in range(3000):
            self.mm.allocate("aa")

        self.assertEqual(len(self.mm.arenas), 1)
        self.assertGreaterEqual(len(self.mm.arenas[0].pools), 2)

    def test_arena_rollover_creates_second_arena(self) -> None:
        # an 8192-byte arena only fits two default pools, so this should
        # force a third arena into existence
        self.mm.arenas.append(Arena(capacity_bytes=8192))

        big = "x" * 128
        for _ in range(100):
            self.mm.allocate(big)

        self.assertGreaterEqual(len(self.mm.arenas), 2)

    def test_deallocate_and_reuse_same_instance(self) -> None:
        self.mm.arenas.append(Arena(capacity_bytes=4096))

        b1 = self.mm.allocate("hello")
        self.mm.allocate("world")
        self.mm.deallocate(b1)
        b3 = self.mm.allocate("!!!!!")

        self.assertIs(b3, b1)

    def test_deallocate_unknown_raises(self) -> None:
        self.mm.arenas.append(Arena(capacity_bytes=4096))

        rogue = Block(size_bytes=8)
        with self.assertRaises(KeyError):
            self.mm.deallocate(rogue)

    def test_stats_shape_contains_expected_keys(self) -> None:
        keys = {
            "arenas",
            "pools",
            "blocks_total",
            "blocks_free",
            "blocks_used",
            "bytes_used_in_pools",
        }
        self.assertTrue(keys.issubset(self.mm.stats().keys()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
