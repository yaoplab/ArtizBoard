"""Theme Manager — Singleton that drives theming for the entire ArtizBoard app.

Adapted from LarcCommon/larccommon/theme.py (ThemeManager + QssHelper).
For Flet: builds ft.Theme objects dynamically from a seed color + palette.
"""

from __future__ import annotations

from typing import Optional, Callable

import flet as ft

from ArtizBoardCommon.colors import (
    Palette, THEME_PALETTES, THEMES_CONFIG,
    BLUE_PALETTE, DARK_PALETTE, SOBRE_PALETTE, CONTRAST_PALETTE,
)
from ArtizBoardCommon.typography import Typography
from ArtizBoardCommon.tokens import DesignTokens, tokens as default_tokens


class ThemeManager:
    """Central theme manager — single source of truth for colors, typography, and tokens.

    Usage:
        tm = ThemeManager()
        tm.set_active("dark")
        page.theme = tm.flet_theme
        page.update()
    """

    def __init__(self, initial_theme: str = "blue"):
        self._on_change: list[Callable] = []
        self._themes: dict[str, Palette] = dict(THEME_PALETTES)
        self._active_name: str = initial_theme
        self._palette: Palette = self._themes.get(initial_theme, BLUE_PALETTE)
        self._typo = Typography(family="Roboto")
        self._tokens = DesignTokens()

    # ── Events ──

    def on_change(self, callback: Callable):
        """Register a callback for theme changes."""
        self._on_change.append(callback)

    def _notify(self):
        for cb in self._on_change:
            cb()

    # ── Properties ──

    @property
    def palette(self) -> Palette:
        return self._palette

    @property
    def typography(self) -> Typography:
        return self._typo

    @property
    def tokens(self) -> DesignTokens:
        return self._tokens

    @property
    def active_name(self) -> str:
        return self._active_name

    @property
    def is_dark(self) -> bool:
        return self._palette.is_dark

    @property
    def hex_seed(self) -> str:
        return self._palette.hex_seed

    @property
    def p(self) -> Palette:
        """Shorthand for palette (matching LarcCommon ds.p convention)."""
        return self._palette

    # ── Theme listing ──

    def names(self) -> list[tuple[str, str]]:
        return [(k, v.label if hasattr(v, 'label') else k.capitalize()) for k, v in self._themes.items()]

    def theme_list(self) -> list[dict]:
        """Returns list of {key, label, seed, is_dark} for UI selectors."""
        return [
            {"key": key, "label": label, "seed": seed, "is_dark": is_dark}
            for key, label, seed, is_dark in THEMES_CONFIG
        ]

    # ── Activation ──

    def set_active(self, name: str) -> bool:
        """Switch to a named theme. Returns True if successful."""
        pal = self._themes.get(name)
        if pal is None:
            return False
        self._active_name = name
        self._palette = pal
        self._notify()
        return True

    # ── Flet theme builder ──

    @property
    def flet_theme(self) -> ft.Theme:
        """Generate a ft.Theme from the current palette.

        This is the main bridge between ArtizBoardCommon and Flet's theming.
        Usage: page.theme = tm.flet_theme
        """
        p = self._palette
        return ft.Theme(
            color_scheme_seed=p.hex_seed,
            use_material3=True,
            font_family=self._typo.family,
            color_scheme=ft.ColorScheme(
                primary=p.primary,
                on_primary=p.on_primary,
                primary_container=p.primary_container,
                on_primary_container=p.on_primary_container,
                secondary=p.secondary,
                on_secondary=p.on_secondary,
                secondary_container=p.secondary_container,
                on_secondary_container=p.on_secondary_container,
                tertiary=p.tertiary,
                on_tertiary=p.on_tertiary,
                tertiary_container=p.tertiary_container,
                on_tertiary_container=p.on_tertiary_container,
                error=p.error,
                on_error=p.on_error,
                error_container=p.error_container,
                on_error_container=p.on_error_container,
                surface=p.surface,
                on_surface=p.on_surface,
                on_surface_variant=p.on_surface_variant,
                outline=p.outline,
                outline_variant=p.outline_variant,
                inverse_surface=p.inverse_surface,
                on_inverse_surface=p.inverse_on_surface,
                inverse_primary=p.inverse_primary,
                shadow=p.shadow,
                surface_container_lowest=p.surface_container_lowest,
                surface_container_low=p.surface_container_low,
                surface_container=p.surface_container,
                surface_container_high=p.surface_container_high,
                surface_container_highest=p.surface_container_highest,
            ),
        )

    # ── Convenience: apply to page ──

    def apply_to(self, page: ft.Page):
        """Apply the current theme to a Flet page."""
        page.theme = self.flet_theme
        page.dark_theme = self.flet_theme
        page.theme_mode = ft.ThemeMode.DARK if self.is_dark else ft.ThemeMode.LIGHT
        page.update()


# Module-level singleton (matching LarcCommon's `theme_manager`)
theme_manager = ThemeManager()
