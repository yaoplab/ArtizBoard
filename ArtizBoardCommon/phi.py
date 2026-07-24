"""Fibonacci & Golden Ratio (Phi) constants and utilities for the design system.

Inspired by LarcCommon/phibuilder/phi/constants.py and scale.py
"""

import math
from enum import IntEnum

SQRT5 = math.sqrt(5)
PHI = (1 + SQRT5) / 2          # 1.618033988749895
PHI_INV = 1 / PHI              # 0.618...
PHI_SQUARED = PHI * PHI        # 2.618...

FIBONACCI = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]


def fibonacci(n: int) -> int:
    """Return the n-th Fibonacci number (fast doubling)."""
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    fib = FIBONACCI
    if n < len(fib):
        return fib[n]
    k = n // 2
    if n % 2 == 0:
        fk = fibonacci(k)
        fk1 = fibonacci(k + 1)
        return fk * (2 * fk1 - fk)
    fk = fibonacci(k)
    fk1 = fibonacci(k + 1)
    return fk * fk + fk1 * fk1


class SpacingToken(IntEnum):
    """Spacing tokens based on Fibonacci sequence (× base_spacing).

    Usage: SpacingToken.MD → 5 × base → 20px (with base=4)
    """
    NONE = 0
    XXS = 1
    XS = 2
    SM = 3
    MD = 5
    LG = 8
    XL = 13
    XXL = 21
    XXXL = 34
    HUGE = 55
    GIANT = 89
    COLOSSAL = 144


class TypeToken(IntEnum):
    """Material Design v3 type scale (in pixels)."""
    LABEL_SM = 11
    LABEL_MD = 12
    LABEL_LG = 14
    BODY_SM = 12
    BODY_MD = 14
    BODY_LG = 16
    TITLE_SM = 14
    TITLE_MD = 16
    TITLE_LG = 22
    HEADLINE_SM = 24
    HEADLINE_MD = 28
    HEADLINE_LG = 32
    DISPLAY_SM = 36
    DISPLAY_MD = 44
    DISPLAY_LG = 52


class Angle(IntEnum):
    ZERO = 0
    PHI_DEG = 137
    PHI_DEG_COMPLEMENT = 222
    QUARTER_CIRCLE = 90
    HALF_CIRCLE = 180
    FULL_CIRCLE = 360

    @property
    def radians(self) -> float:
        return math.radians(self.value)
