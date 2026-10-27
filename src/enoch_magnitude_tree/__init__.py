# SPDX-License-Identifier: MIT
"""enoch_magnitude_tree — associative tree keyed by binary-logarithm magnitudes.

A single concrete class, :class:`MagnitudeTree`, is re-exported from
:mod:`enoch_magnitude_tree.core` so callers can write::

    from enoch_magnitude_tree import MagnitudeTree

"""

from .core import MagnitudeTree

__all__ = ["MagnitudeTree"]
