# SPDX-License-Identifier: MIT
"""Tests for enoch_magnitude_tree.core.

Run with::

    PYTHONPATH=src python -m unittest discover -s tests
"""

import unittest

from enoch_magnitude_tree.core import MagnitudeTree, magnitude_key


class TestMagnitudeKey(unittest.TestCase):
    def test_zero_is_zero(self):
        self.assertEqual(magnitude_key(0), 0)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            magnitude_key(-1)

    def test_power_of_two_has_zero_suffix(self):
        # n = 2**k: highest bit at position k, suffix is 0, popcount 0.
        self.assertEqual(magnitude_key(1), 0)
        self.assertEqual(magnitude_key(2), 1)
        self.assertEqual(magnitude_key(4), 2)
        self.assertEqual(magnitude_key(8), 3)
        self.assertEqual(magnitude_key(16), 4)

    def test_three_collides_with_power(self):
        # n=3: k=1, suffix bits = 1, popcount=1 -> key=2.
        # n=5: k=2, suffix bits = 01, popcount=1 -> key=3.
        self.assertEqual(magnitude_key(3), 2)
        self.assertEqual(magnitude_key(5), 3)

    def test_seven(self):
        # n=7: k=2, suffix bits = 11, popcount=2 -> key=4.
        self.assertEqual(magnitude_key(7), 4)

    def test_eleven(self):
        # n=11: binary 1011, k=3, suffix = 011, popcount=2 -> key=5.
        self.assertEqual(magnitude_key(11), 5)

    def test_keys_are_nonnegative(self):
        for n in range(0, 256):
            self.assertGreaterEqual(magnitude_key(n), 0)

    def test_keys_are_deterministic_under_repeat(self):
        ns = list(range(0, 128))
        first = [magnitude_key(n) for n in ns]
        second = [magnitude_key(n) for n in ns]
        self.assertEqual(first, second)

    def test_large_integer_exact(self):
        # 2**60 must not lose precision: key should be exactly 60.
        self.assertEqual(magnitude_key(1 << 60), 60)


class TestTree(unittest.TestCase):
    def test_insert_and_lookup(self):
        t = MagnitudeTree()
        t.insert(4, "four")
        bucket = t.lookup(4)
        self.assertEqual(bucket, [(4, "four")])

    def test_collisions_share_bucket(self):
        t = MagnitudeTree()
        # n=3 (key 2) and n=6 (k=2, suffix=10, popcount=1 -> key 3) do NOT
        # collide; pick two that do: n=3 and n=3+1=... recompute.
        # n=3: key 2.  n=2: key 1.  Need same key -> same k and same suffix popcount.
        # n=5: k=2, suffix=01, pc=1 -> key 3.
        # n=6: k=2, suffix=10, pc=1 -> key 3.  These collide.
        t.insert(5, "five")
        t.insert(6, "six")
        b5 = t.lookup(5)
        b6 = t.lookup(6)
        self.assertEqual(b5, b6)
        self.assertEqual(sorted(b5), [(5, "five"), (6, "six")])

    def test_lookup_empty_bucket(self):
        t = MagnitudeTree()
        self.assertEqual(t.lookup(100), [])

    def test_len_tracks_inserts(self):
        t = MagnitudeTree()
        self.assertEqual(len(t), 0)
        t.insert(1, "a")
        t.insert(2, "b")
        t.insert(3, "c")
        self.assertEqual(len(t), 3)

    def test_remove_key_returns_count(self):
        t = MagnitudeTree()
        t.insert(5, "five")
        t.insert(6, "six")
        removed = t.remove_key(3)  # shared key for 5 and 6
        self.assertEqual(removed, 2)
        self.assertEqual(len(t), 0)
        self.assertEqual(t.lookup(5), [])

    def test_remove_missing_key_returns_zero(self):
        t = MagnitudeTree()
        self.assertEqual(t.remove_key(99), 0)

    def test_keys_sorted(self):
        t = MagnitudeTree()
        t.insert(16, "x")  # key 4
        t.insert(1, "y")    # key 0
        t.insert(4, "z")    # key 2
        self.assertEqual(t.keys(), [0, 2, 4])

    def test_contains(self):
        t = MagnitudeTree()
        t.insert(7, "seven")
        self.assertIn(7, t)
        self.assertNotIn(8, t)

    def test_contains_rejects_negative_and_bool(self):
        t = MagnitudeTree()
        t.insert(1, "one")
        self.assertNotIn(-1, t)
        self.assertNotIn(True, t)  # bool is a subclass of int; exclude it.

    def test_iteration_order(self):
        t = MagnitudeTree()
        t.insert(4, "z")   # key 2
        t.insert(1, "y")    # key 0
        t.insert(2, "x")    # key 1
        triples = list(t)
        self.assertEqual(
            triples,
            [(0, 1, "y"), (1, 2, "x"), (2, 4, "z")],
        )

    def test_lookup_returns_copy(self):
        t = MagnitudeTree()
        t.insert(5, "five")
        b = t.lookup(5)
        b.clear()
        # Internal state must be untouched.
        self.assertEqual(t.lookup(5), [(5, "five")])

    def test_zero_bucket(self):
        t = MagnitudeTree()
        t.insert(0, "zero")
        t.insert(1, "one")  # key 0 as well (k=0, suffix empty, pc=0)
        b = t.lookup(0)
        self.assertEqual(sorted(b), [(0, "zero"), (1, "one")])


if __name__ == "__main__":
    unittest.main()
