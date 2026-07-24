"""ArtizBoardCommon — Design System & Shared Modules for ArtizBoard (Flet).

Fondation visuelle et fonctionnelle inspirée de LarcCommon (PySide6).
Traduit les concepts Material Design v3 + Fibonacci + Nombre d'Or pour Flet.

Usage:
    from ArtizBoardCommon import ds, tm
    ds.apply(page)
    page.add(ft.Text("Bonjour", style=ds.textstyle("headline_medium")))
"""

from ArtizBoardCommon.design_system import DesignSystem, ds
from ArtizBoardCommon.theme import ThemeManager, theme_manager as tm
from ArtizBoardCommon.colors import (
    Palette, THEME_PALETTES, THEMES_CONFIG,
    BLUE_PALETTE, DARK_PALETTE, SOBRE_PALETTE, CONTRAST_PALETTE,
    palette_from_seed,
)
from ArtizBoardCommon.typography import Typography, Typography as Typo, TypeStyle, FontWeight
from ArtizBoardCommon.tokens import DesignTokens, tokens, spacing
from ArtizBoardCommon.phi import (
    PHI, PHI_INV, PHI_SQUARED, SQRT5,
    SpacingToken, TypeToken, Angle, fibonacci,
)
from ArtizBoardCommon.shapes import Shape, BorderRadius, ElevationLevel, Shadow
import ArtizBoardCommon.config_loader as config_loader
import ArtizBoardCommon.icons as icons
import ArtizBoardCommon.components as components

__all__ = [
    "DesignSystem", "ds",
    "ThemeManager", "tm",
    "Palette", "THEME_PALETTES", "THEMES_CONFIG",
    "BLUE_PALETTE", "DARK_PALETTE", "SOBRE_PALETTE", "CONTRAST_PALETTE",
    "palette_from_seed",
    "Typography", "Typo", "TypeStyle", "FontWeight",
    "DesignTokens", "tokens", "spacing",
    "PHI", "PHI_INV", "PHI_SQUARED", "SQRT5",
    "SpacingToken", "TypeToken", "Angle", "fibonacci",
    "Shape", "BorderRadius", "ElevationLevel", "Shadow",
    "icons",
    "config_loader",
    "components",
]
