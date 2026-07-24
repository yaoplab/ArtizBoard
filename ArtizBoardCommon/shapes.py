"""Shape & Elevation system — Material Design v3 border radii and shadow levels.

Adapted from LarcCommon/phibuilder/theme/shape.py and elevation.py
"""

from dataclasses import dataclass
from enum import Enum

import flet as ft

# ── Border Radius ──


@dataclass(frozen=True)
class BorderRadius:
    top_left: int = 0
    top_right: int = 0
    bottom_right: int = 0
    bottom_left: int = 0

    @classmethod
    def all(cls, r: int):
        return cls(r, r, r, r)

    def to_flet(self) -> ft.BorderRadius:
        return ft.BorderRadius(
            self.top_left, self.top_right,
            self.bottom_right, self.bottom_left,
        )


M3_SHAPES = {
    "none": BorderRadius.all(0),
    "xs": BorderRadius.all(4),
    "sm": BorderRadius.all(8),
    "md": BorderRadius.all(12),
    "lg": BorderRadius.all(16),
    "xl": BorderRadius.all(28),
    "full": BorderRadius.all(9999),
}


class Shape(str, Enum):
    NONE = "none"
    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"
    FULL = "full"

    @property
    def radius(self) -> BorderRadius:
        return M3_SHAPES[self.value]


# ── Elevation (shadows) ──

@dataclass(frozen=True)
class Shadow:
    offset_x: int = 0
    offset_y: int = 1
    blur: int = 3
    spread: int = 0
    opacity: float = 0.3


M3_ELEVATION = {
    0: [],
    1: [Shadow(0, 1, 3, 0, 0.3), Shadow(0, 1, 2, 0, 0.15)],
    2: [Shadow(0, 1, 5, 0, 0.3), Shadow(0, 2, 2, 0, 0.15)],
    3: [Shadow(0, 1, 8, 0, 0.3), Shadow(0, 3, 4, 0, 0.15)],
    4: [Shadow(0, 2, 10, 0, 0.3), Shadow(0, 4, 5, 0, 0.15)],
    5: [Shadow(0, 4, 12, 0, 0.3), Shadow(0, 6, 7, 0, 0.15)],
}


class ElevationLevel(int, Enum):
    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5

    @property
    def shadows(self) -> list[Shadow]:
        return M3_ELEVATION[self.value]
