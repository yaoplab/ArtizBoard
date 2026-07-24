"""ArtizBoard Design System — Main entry point.

Singleton `ds` that combines color, typography, spacing, shapes, and elevation.
Inspired by LarcCommon/larccommon/design_system.py
Provides a unified API matching the LarcCommon `ds.*` conventions but for Flet.

RÈGLE ABSOLUE : ZÉRO HARDCODING DANS L'UI.
Toutes les tailles, espacements, couleurs et polices passent par ce module.
"""

from __future__ import annotations

from typing import Optional

import flet as ft

from ArtizBoardCommon.theme import ThemeManager, theme_manager as _default_tm
from ArtizBoardCommon.colors import Palette
from ArtizBoardCommon.typography import Typography, TypeStyle
from ArtizBoardCommon.tokens import DesignTokens, tokens as default_tokens
from ArtizBoardCommon.phi import SpacingToken, TypeToken, PHI, fibonacci
from ArtizBoardCommon.shapes import Shape, ElevationLevel


class DesignSystem:
    """Central Design System for ArtizBoard apps.

    Singleton usage:
        from ArtizBoardCommon import ds
        ds.theme_manager.set_active("dark")
        ds.apply(page)
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        self._tm = theme_manager or _default_tm
        self.GOLDEN = PHI
        self.border_width = 1
        self.radius_none = 0

        # Shape shortcuts
        self.SHAPE_NONE = Shape.NONE
        self.SHAPE_XS = Shape.XS
        self.SHAPE_SM = Shape.SM
        self.SHAPE_MD = Shape.MD
        self.SHAPE_LG = Shape.LG
        self.SHAPE_XL = Shape.XL
        self.SHAPE_FULL = Shape.FULL

        # Elevation shortcuts
        self.ELEV_0 = ElevationLevel.LEVEL_0
        self.ELEV_1 = ElevationLevel.LEVEL_1
        self.ELEV_2 = ElevationLevel.LEVEL_2
        self.ELEV_3 = ElevationLevel.LEVEL_3
        self.ELEV_4 = ElevationLevel.LEVEL_4
        self.ELEV_5 = ElevationLevel.LEVEL_5

    # ── Properties ──

    @property
    def tm(self) -> ThemeManager:
        return self._tm

    @property
    def p(self) -> Palette:
        """Shorthand: ds.p.primary, ds.p.surface, etc."""
        return self._tm.palette

    @property
    def colors(self) -> Palette:
        return self._tm.palette

    @property
    def typo(self) -> Typography:
        return self._tm.typography

    @property
    def t(self) -> DesignTokens:
        return self._tm.tokens

    @property
    def tokens(self) -> DesignTokens:
        return self._tm.tokens

    # ── Spacing (Fibonacci) ──

    def sp(self, token: SpacingToken) -> int:
        return int(token) * 4

    @property
    def space_xxs(self) -> int: return self.sp(SpacingToken.XXS)
    @property
    def space_xs(self) -> int: return self.sp(SpacingToken.XS)
    @property
    def space_sm(self) -> int: return self.sp(SpacingToken.SM)
    @property
    def space_md(self) -> int: return self.sp(SpacingToken.MD)
    @property
    def space_lg(self) -> int: return self.sp(SpacingToken.LG)
    @property
    def space_xl(self) -> int: return self.sp(SpacingToken.XL)
    @property
    def space_xxl(self) -> int: return self.sp(SpacingToken.XXL)
    @property
    def space_xxxl(self) -> int: return self.sp(SpacingToken.XXXL)

    # ── Golden ratio proportions ──

    def golden_width(self, height: int) -> int:
        return int(height * self.GOLDEN)

    def golden_height(self, width: int) -> int:
        return int(width / self.GOLDEN)

    def golden_split(self, total: int) -> tuple[int, int]:
        small = int(total / (self.GOLDEN + 1))
        large = total - small
        return large, small

    # ── Shape helpers ──

    def border_radius(self, shape: Shape) -> ft.BorderRadius:
        return shape.radius.to_flet()

    def border_radius_all(self, r: int) -> ft.BorderRadius:
        return ft.BorderRadius(r, r, r, r)

    # ── Component dimensions (matching LarcCommon ds) ──

    @property
    def field_height(self) -> int:
        return self.t.field_height

    @property
    def button_height(self) -> int:
        return self.t.button_height

    @property
    def header_height(self) -> int:
        return self.t.header_height

    @property
    def icon_md(self) -> int:
        return self.t.icon_md

    @property
    def icon_sm(self) -> int:
        return self.t.icon_sm

    @property
    def icon_lg(self) -> int:
        return self.t.icon_lg

    # ── Theme management ──

    def switch_theme(self, name: str) -> bool:
        return self._tm.set_active(name)

    def apply(self, page: ft.Page):
        """Apply the design system to a Flet page."""
        self._tm.apply_to(page)

    # ── Typography shortcuts ──

    def textstyle(self, name: str, color: str = "") -> ft.TextStyle:
        return self._tm.typography.textstyle(name, color)

    @property
    def font_h1(self) -> TypeStyle:
        return self._tm.typography.headline_medium

    @property
    def font_h2(self) -> TypeStyle:
        return self._tm.typography.title_large

    @property
    def font_title(self) -> TypeStyle:
        return self._tm.typography.title_medium

    @property
    def font_body(self) -> TypeStyle:
        return self._tm.typography.body_medium

    @property
    def font_small(self) -> TypeStyle:
        return self._tm.typography.body_small


# Singleton global (matching LarcCommon's `ds`)
ds = DesignSystem()
