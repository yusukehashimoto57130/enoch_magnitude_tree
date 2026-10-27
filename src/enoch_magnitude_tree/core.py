# SPDX-License-Identifier: MIT
"""Magnitude tree implementation.

The tree is a shallow associative container indexed by a deterministic
"magnitude key" derived from each nonnegative integer ``n``.

Interpretation of the brief (stated plainly so the tests match the code)
-------------------------------------------------------------------------

For ``n == 0`` the key is ``0`` (a special, fixed bucket).

For ``n >= 1`` the key is ``floor(log2(n)) + suffix`` where the suffix is
``popcount(clamp(n-bit suffix))``.  We interpret the bracketed clause as:

1. Compute ``k = floor(log2(n))`` — the position of the highest set bit,
   i.e. ``n.bit_length() - 1``.
2. Extract the low ``k`` bits of ``n`` (the bits strictly below the highest
   set bit).  This is the "n-bit suffix": the suffix is at most ``k`` bits wide.
3. Clamp that suffix to ``k`` bits via a mask so it can never exceed the width
   it was defined for (this is what "popcount-clamped" guards against in the
   brief).  For a properly formed ``n`` the suffix already fits, but the clamp
   makes the function total on every nonnegative integer.
4. Take the Hamming weight (popcount) of the clamped suffix.

The suffix therefore ranges over ``[0, k]`` and the full key ranges over
``[k, 2k]``, so every ``n`` maps to a nonnegative integer key with no gaps for
fixed ``k``.  Two different ``n`` values with the same highest-bit position and
the same suffix popcount collide on the same key by design: the tree is a
*bucketed* associative structure, not an injective map.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple

__all__ = ["MagnitudeTree"]


def _floor_log2(n: int) -> int:
    """Return ``floor(log2(n))`` for ``n >= 1`` via integer arithmetic.

    We avoid :mod:`math` floating-point functions because they lose precision
    past 2**53 and the brief requires exact, deterministic keys for every
    nonnegative integer.
    """
    return n.bit_length() - 1


def magnitude_key(n: int) -> int:
    """Return the magnitude key for a nonnegative integer ``n``.

    ``n == 0`` maps to ``0``.  For ``n >= 1`` the key is
    ``floor(log2(n)) + popcount(low floor(log2(n)) bits of n)``.

    Raises :class:`ValueError` if ``n`` is negative — the brief scopes the
    function to *nonnegative* integers, so we refuse silently-broken input
    rather than picking an arbitrary convention for negatives.
    """
    if n < 0:
        raise ValueError("magnitude_key requires a nonnegative integer")
    if n == 0:
        return 0
    k = _floor_log2(n)
    suffix_mask = (1 << k) - 1
    suffix = n & suffix_mask
    return k + suffix.bit_count()


class MagnitudeTree:
    """Associative bucket tree keyed by :func:`magnitude_key`.

    Each bucket is a list of ``(n, value)`` pairs in insertion order.  Lookups
    return a *copy* of the matching bucket so callers cannot mutate internal
    state by accident — the tree's invariants are easier to reason about when
    the only mutation paths are :meth:`insert` and :meth:`remove`.
    """

    __slots__ = ("_buckets", "_size")

    def __init__(self) -> None:
        self._buckets: Dict[int, List[Tuple[int, Any]]] = {}
        self._size: int = 0

    # ---- core operations -------------------------------------------------

    def insert(self, n: int, value: Any) -> None:
        """Insert ``(n, value)`` into the bucket for ``magnitude_key(n)``."""
        key = magnitude_key(n)
        self._buckets.setdefault(key, []).append((n, value))
        self._size += 1

    def lookup(self, n: int) -> List[Tuple[int, Any]]:
        """Return a shallow copy of every ``(n_i, v_i)`` pair in ``n``'s bucket.

        The returned list is empty if the bucket does not exist yet.
        """
        return list(self._buckets.get(magnitude_key(n), ()))

    def remove_key(self, key: int) -> int:
        """Delete the entire bucket for ``key`` and return the pair count removed.

        Removing a whole bucket is O(len(bucket)); removing individual entries
        by their original ``n`` would require a full scan of every bucket and
        an ambiguity policy (remove first? all?), so we expose only the
        unambiguous operation.
        """
        bucket = self._buckets.pop(key, None)
        if bucket is None:
            return 0
        removed = len(bucket)
        self._size -= removed
        return removed

    # ---- introspection ---------------------------------------------------

    def keys(self) -> List[int]:
        """Return occupied magnitude keys in ascending order."""
        return sorted(self._buckets)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, n: object) -> bool:
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            return False
        bucket = self._buckets.get(magnitude_key(n))
        return bucket is not None and any(pair[0] == n for pair in bucket)

    def __iter__(self) -> Iterator[Tuple[int, int, Any]]:
        """Yield ``(key, n, value)`` triples ordered by key then insertion order.

        Iteration order is fully determined by the integer keys, which keeps
        tests deterministic without sorting at the call site.
        """
        for key in sorted(self._buckets):
            for n, value in self._buckets[key]:
                yield key, n, value
