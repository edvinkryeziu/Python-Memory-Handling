# Python Memory Handling

A small simulation of how a memory allocator works, built with Python
classes: **arenas** contain **pools**, pools contain **blocks**, and a
**memory manager** ties it all together.

I made this to get a feel for allocator concepts (arenas, pooling,
first/best-fit, block reuse) by actually implementing a toy version instead
of just reading about them.

## How it fits together

- `Block` — the smallest unit. Stores one value, knows whether it's free.
- `Pool` — a fixed-size collection of blocks. Keeps freed blocks around so
  they can be handed back out instead of creating new ones.
- `Arena` — a bigger region made up of several pools.
- `MemoryManager` — a singleton that owns all the arenas. This is what you
  actually call `allocate()` / `deallocate()` on. It figures out which pool
  a value should go into, and creates new pools/arenas automatically once
  existing ones fill up.

There's no real memory being managed here — `_sizeof()` just makes up a
byte cost per value (an `int` "costs" 8 bytes, a `str` costs `len(value)`,
etc.) so that pools and arenas fill up realistically during a run.

## Running it

No third-party dependencies, just the standard library.

```bash
python memory_manager.py
```

```python
from memory_manager import MemoryManager

mm = MemoryManager()
b1 = mm.allocate("hello")           # 5 bytes
b2 = mm.allocate([1, 2, 3, 4, 5])   # 40 bytes
mm.deallocate(b1)                   # freed, but kept for reuse
b3 = mm.allocate("world!")          # reuses b1's block

print(b3 is b1)     # True
print(mm.stats())
```

Tests:

```bash
python -m unittest test_memory.py -v
```

## Pool selection

Allocation defaults to first-fit (first pool with enough room). There's
also a best-fit implementation you can swap in:

```python
mm.set_pick_policy(mm._best_fit)
```

## Notes

- A deallocated block stays attached to its pool — only its `is_free` flag
  and stored value change, so the same instance gets reused later.
- Sizes are simulated (`size_bytes`), not actual memory usage.
