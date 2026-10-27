# enoch_magnitude_tree

A small associative tree that buckets `(n, value)` pairs by a deterministic magnitude key derived from each nonnegative integer `n`. For `n == 0` the key is `0`; for `n >= 1` it is `floor(log2(n)) + popcount(low floor(log2(n)) bits of n)`.

```python
from enoch_magnitude_tree import MagnitudeTree

t = MagnitudeTree()
t.insert(5, "five")
t.insert(6, "six")     # same key as 5 -> same bucket
print(t.lookup(5))     # [(5, 'five'), (6, 'six')]
print(t.keys())        # [3]
print(len(t))          # 2
for key, n, value in t:
    print(key, n, value)
```

Exported names: `MagnitudeTree` (class), with methods `insert(n, value)`, `lookup(n) -> list[(int, Any)]`, `remove_key(key) -> int`, `keys() -> list[int]`, plus `__len__`, `__contains__`, and `__iter__`. The helper `magnitude_key(n) -> int` is also importable from `enoch_magnitude_tree.core`.

## Why this exists

The library answers a narrow question: can you group arbitrary nonnegative integers into stable, collision-prone buckets whose membership depends only on the integer itself, so that lookups are reproducible across processes and there are no hidden parameters to tune? The trade-off is that the mapping is deliberately not injective — two integers with the same highest-bit position and the same suffix popcount land in the same bucket. If you need a one-to-one map, use a plain `dict`.

## The awkward edge

`n = 0` and `n = 1` both map to key `0` (for `n = 1`, `floor(log2(1)) = 0` and the suffix is empty, so its popcount is `0`). They share a bucket. This is intentional and is tested. Also, `bool` values are rejected by `__contains__` even though `bool` is a subclass of `int`, because mixing `True` with the integer `1` would make membership tests ambiguous.
