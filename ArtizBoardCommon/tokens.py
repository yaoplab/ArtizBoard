"""Design Tokens — Centralized spacing, padding, and component sizing.

Based on Fibonacci scale (base_spacing=4) and Material Design v3 conventions.
Adapted from LarcCommon's DesignTokens and design_system.py patterns.
"""

from dataclasses import dataclass, field
from typing import Optional

from ArtizBoardCommon.phi import SpacingToken

# Flet uses `margin` and `padding` as `ft.Control.margin` / `ft.Control.padding`.
# These tokens produce plain int values for use with `ft.margin.all()`, etc.

_BASE = 4


def spacing(token: SpacingToken) -> int:
    """Resolve a SpacingToken to its pixel value."""
    return int(token) * _BASE


@dataclass
class DesignTokens:
    """All design tokens for ArtizBoard.

    All values in pixels. These are the SINGLE SOURCE OF TRUTH.
    No hardcoded spacing in UI code.
    """
    # Core spacing (Fibonacci × 4)
    space_xxs: int = 4    # 1 × 4
    space_xs: int = 8     # 2 × 4
    space_sm: int = 12    # 3 × 4
    space_md: int = 20    # 5 × 4
    space_lg: int = 32    # 8 × 4
    space_xl: int = 52    # 13 × 4
    space_xxl: int = 84   # 21 × 4
    space_xxxl: int = 136 # 34 × 4

    # Border radii
    radius_none: int = 0
    radius_xs: int = 4
    radius_sm: int = 8
    radius_md: int = 12
    radius_lg: int = 16
    radius_xl: int = 28
    radius_full: int = 9999

    # Component sizing
    field_height: int = 32    # Input fields
    button_height: int = 52   # Buttons (M3 touch target)
    header_height: int = 52   # Top bars
    icon_md: int = 32         # Medium icons
    icon_sm: int = 18         # Small icons
    icon_lg: int = 48         # Large icons
    table_row_min: int = 42   # Table row min height

    # Padding tokens (fields, buttons, labels)
    field_pad_v: int = 8
    field_pad_h: int = 12
    btn_pad_v: int = 8
    btn_pad_h: int = 20
    btn_sm_pad_v: int = 6
    btn_sm_pad_h: int = 16
    label_pad_v: int = 6
    label_pad_h: int = 0

    # Borders
    border_width: int = 1
    btn_border: int = 1

    # Grid
    grid_columns: int = 12
    grid_gutter: int = 20  # space_md
    grid_margin: int = 32  # space_lg

    # Cards
    card_min_width: int = 280
    card_max_width: int = 400

    # Sidebar
    sidebar_width: int = 260
    sidebar_collapsed: int = 72

    # Golden ratio (macro proportions)
    golden: float = 1.618033988749895

    def golden_width(self, height: int) -> int:
        return int(height * self.golden)

    def golden_height(self, width: int) -> int:
        return int(width / self.golden)

    def golden_split(self, total: int) -> tuple[int, int]:
        small = int(total / (self.golden + 1))
        large = total - small
        return large, small


# Singleton
tokens = DesignTokens()
