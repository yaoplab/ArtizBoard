"""Material Design v3 Typography — Type scale for Flet.

Adapted from LarcCommon/phibuilder/theme/typo.py
Each style maps to flet.TextStyle for use in themes and controls.
"""

from dataclasses import dataclass
from enum import IntEnum

import flet as ft


class FontWeight(IntEnum):
    THIN = 100
    EXTRA_LIGHT = 200
    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMI_BOLD = 600
    BOLD = 700
    EXTRA_BOLD = 800
    BLACK = 900


@dataclass(frozen=True)
class TypeStyle:
    family: str = "Roboto"
    size: int = 14
    weight: FontWeight = FontWeight.REGULAR
    height: float = 1.5
    letter_spacing: float = 0.0

    def to_textstyle(self, color: str = "") -> ft.TextStyle:
        _FW_MAP = {
            100: ft.FontWeight.W_100,
            200: ft.FontWeight.W_200,
            300: ft.FontWeight.W_300,
            400: ft.FontWeight.W_400,
            500: ft.FontWeight.W_500,
            600: ft.FontWeight.W_600,
            700: ft.FontWeight.W_700,
            800: ft.FontWeight.W_800,
            900: ft.FontWeight.W_900,
        }
        return ft.TextStyle(
            font_family=self.family,
            size=self.size,
            weight=_FW_MAP.get(self.weight.value, ft.FontWeight.W_400),
            height=self.height,
            letter_spacing=self.letter_spacing,
            color=color or None,
        )


M3_TYPOGRAPHY = {
    "display_large":   TypeStyle(size=57, weight=FontWeight.REGULAR,  height=1.12, letter_spacing=-0.25),
    "display_medium":  TypeStyle(size=45, weight=FontWeight.REGULAR,  height=1.15, letter_spacing=0.0),
    "display_small":   TypeStyle(size=36, weight=FontWeight.REGULAR,  height=1.22, letter_spacing=0.0),
    "headline_large":  TypeStyle(size=32, weight=FontWeight.BOLD,     height=1.25, letter_spacing=0.0),
    "headline_medium": TypeStyle(size=28, weight=FontWeight.BOLD,     height=1.28, letter_spacing=0.0),
    "headline_small":  TypeStyle(size=24, weight=FontWeight.BOLD,     height=1.33, letter_spacing=0.0),
    "title_large":     TypeStyle(size=22, weight=FontWeight.BOLD,     height=1.27, letter_spacing=0.0),
    "title_medium":    TypeStyle(size=16, weight=FontWeight.MEDIUM,   height=1.50, letter_spacing=0.15),
    "title_small":     TypeStyle(size=14, weight=FontWeight.MEDIUM,   height=1.43, letter_spacing=0.1),
    "body_large":      TypeStyle(size=16, weight=FontWeight.REGULAR,  height=1.50, letter_spacing=0.5),
    "body_medium":     TypeStyle(size=14, weight=FontWeight.REGULAR,  height=1.43, letter_spacing=0.25),
    "body_small":      TypeStyle(size=12, weight=FontWeight.REGULAR,  height=1.33, letter_spacing=0.4),
    "label_large":     TypeStyle(size=14, weight=FontWeight.MEDIUM,   height=1.43, letter_spacing=0.1),
    "label_medium":    TypeStyle(size=12, weight=FontWeight.MEDIUM,   height=1.33, letter_spacing=0.5),
    "label_small":     TypeStyle(size=11, weight=FontWeight.MEDIUM,   height=1.45, letter_spacing=0.5),
}


class Typography:
    """Typography system — wraps all M3 type styles for Flet.

    Usage:
        ds.typo.headline_medium → TypeStyle
        ds.typo.headline_medium.to_textstyle() → ft.TextStyle
        ds.typo.body_md → 14px (size shortcut)
    """

    def __init__(self, family: str = "Roboto"):
        self.family = family
        self._styles = {
            name: TypeStyle(family=family, size=s.size, weight=s.weight,
                            height=s.height, letter_spacing=s.letter_spacing)
            for name, s in M3_TYPOGRAPHY.items()
        }

    def __getattr__(self, name: str) -> TypeStyle:
        key = name.replace("_", "_")
        if key in self._styles:
            return self._styles[key]
        # Also support shortcuts like `body_md` → 14
        raise AttributeError(f"Typography has no style '{name}'")

    @property
    def all(self) -> dict[str, TypeStyle]:
        return dict(self._styles)

    @property
    def body_md(self) -> int:
        return TypeToken.BODY_MD

    def textstyle(self, name: str, color: str = "") -> ft.TextStyle:
        """Quick access: ds.typo.textstyle('headline_medium', color='...')"""
        s = self._styles.get(name)
        if s is None:
            raise KeyError(f"Unknown typography style '{name}'")
        return s.to_textstyle(color)
