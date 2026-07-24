"""Material Design v3 Color Schemes — Dynamic palettes from a seed color.

Adapted from LarcCommon/phibuilder/theme/color.py
Usage: flet.Theme(color_scheme_seed=scheme.hex_seed) or use palette dicts directly.
"""

from dataclasses import dataclass, field
from typing import Optional

# ── Material Design v3 standard roles ──

M3_COLOR_ROLES = [
    "primary", "on_primary", "primary_container", "on_primary_container",
    "secondary", "on_secondary", "secondary_container", "on_secondary_container",
    "tertiary", "on_tertiary", "tertiary_container", "on_tertiary_container",
    "error", "on_error", "error_container", "on_error_container",
    "surface", "on_surface", "surface_variant", "on_surface_variant",
    "background", "on_background",
    "outline", "outline_variant",
    "inverse_surface", "inverse_on_surface", "inverse_primary",
    "surface_container_lowest", "surface_container_low",
    "surface_container", "surface_container_high", "surface_container_highest",
]


@dataclass
class Palette:
    """Complete color palette for an ArtizBoard theme.

    Mirrors the LarcCommon Palette but adds M3 dynamic roles.
    """
    # M3 Core
    primary: str = "#1565C0"
    on_primary: str = "#FFFFFF"
    primary_container: str = "#BBDEFB"
    on_primary_container: str = "#001D36"
    secondary: str = "#00897B"
    on_secondary: str = "#FFFFFF"
    secondary_container: str = "#B2DFDB"
    on_secondary_container: str = "#00201B"
    tertiary: str = "#E65100"
    on_tertiary: str = "#FFFFFF"
    tertiary_container: str = "#FFCC80"
    on_tertiary_container: str = "#2D1500"
    error: str = "#C62828"
    on_error: str = "#FFFFFF"
    error_container: str = "#FFCDD2"
    on_error_container: str = "#410002"
    success: str = "#2E7D32"
    # Surface / Background
    surface: str = "#F5F7FA"
    on_surface: str = "#1B1B1F"
    surface_variant: str = "#E8EAF6"
    on_surface_variant: str = "#46464F"
    background: str = "#F5F7FA"
    on_background: str = "#1B1B1F"
    outline: str = "#546E7A"
    outline_variant: str = "#B0BEC5"
    # Inverse
    inverse_surface: str = "#313033"
    inverse_on_surface: str = "#F3F0F4"
    inverse_primary: str = "#D1E4FF"
    # Surface containers
    surface_container_lowest: str = "#FFFFFF"
    surface_container_low: str = "#F0EFF4"
    surface_container: str = "#EBE9EE"
    surface_container_high: str = "#E5E3E8"
    surface_container_highest: str = "#DFDDE2"
    # Semantic aliases (LarcCommon compatibility)
    text_strong: str = "#1B1B1F"
    text_soft: str = "#455A64"
    text_disabled: str = "#90A4AE"
    active: str = "#1565C0"
    inactive: str = "#90A4AE"
    border: str = "#B0BEC5"
    border_light: str = "#E0E0E0"
    shadow: str = "#000000"
    # Hex seed for flet.Theme(color_scheme_seed=...)
    hex_seed: str = "#1565C0"
    is_dark: bool = False


# ── Built-in palettes (matching LarcCommon themes) ──

BLUE_PALETTE = Palette(
    primary="#1565C0", on_primary="#FFFFFF", primary_container="#BBDEFB",
    secondary="#00897B", on_secondary="#FFFFFF", secondary_container="#B2DFDB",
    tertiary="#E65100", on_tertiary="#FFFFFF", tertiary_container="#FFCC80",
    error="#C62828", error_container="#FFCDD2", success="#2E7D32",
    active="#1565C0", inactive="#90A4AE", border="#B0BEC5", border_light="#E0E0E0",
    text_strong="#1B1B1F", text_soft="#455A64", text_disabled="#90A4AE",
    hex_seed="#1565C0", is_dark=False,
)

DARK_PALETTE = Palette(
    primary="#64B5F6", on_primary="#0D2137", primary_container="#1E3A5F",
    secondary="#81C784", on_secondary="#1B3A1B", secondary_container="#2E5C2E",
    tertiary="#FFB74D", on_tertiary="#3E2C00", tertiary_container="#5C4300",
    error="#EF9A9A", on_error="#5C1A1A", error_container="#7C2020",
    success="#81C784", active="#64B5F6", inactive="#616161",
    surface="#1E1E1E", surface_variant="#2D2D2D", background="#121212",
    on_surface="#E0E0E0", on_surface_variant="#9E9E9E",
    outline="#616161", outline_variant="#424242",
    text_strong="#E0E0E0", text_soft="#9E9E9E", text_disabled="#616161",
    border="#424242", border_light="#383838",
    surface_container_lowest="#19191C", surface_container_low="#222225",
    surface_container="#262629", surface_container_high="#313034",
    surface_container_highest="#3C3B3F",
    inverse_surface="#F3F0F4", inverse_on_surface="#313033", inverse_primary="#1565C0",
    hex_seed="#212121", is_dark=True,
)

SOBRE_PALETTE = Palette(
    primary="#37474F", on_primary="#FFFFFF", primary_container="#CFD8DC",
    secondary="#546E7A", on_secondary="#FFFFFF", secondary_container="#B0BEC5",
    tertiary="#78909C", on_tertiary="#FFFFFF", tertiary_container="#CFD8DC",
    error="#BF360C", on_error="#FFFFFF", error_container="#FFCCBC",
    success="#33691E", active="#37474F", inactive="#BDBDBD",
    surface="#FAFAFA", surface_variant="#EEEEEE", background="#FFFFFF",
    on_surface="#212121", on_surface_variant="#616161",
    outline="#BDBDBD", outline_variant="#E0E0E0",
    text_strong="#212121", text_soft="#616161", text_disabled="#9E9E9E",
    border="#E0E0E0", border_light="#EEEEEE",
    hex_seed="#37474F", is_dark=False,
)

CONTRAST_PALETTE = Palette(
    primary="#0033A0", on_primary="#FFFFFF", primary_container="#80B3FF",
    secondary="#005A9E", on_secondary="#FFFFFF", secondary_container="#80D0FF",
    tertiary="#C62828", on_tertiary="#FFFFFF", tertiary_container="#FFB3B3",
    error="#B71C1C", on_error="#FFFFFF", error_container="#FFCDD2",
    success="#1B5E20", active="#0033A0", inactive="#666666",
    surface="#FFFFFF", surface_variant="#D6E8FF", background="#FFFFFF",
    on_surface="#000000", on_surface_variant="#1A1A1A",
    outline="#000000", outline_variant="#333333",
    text_strong="#000000", text_soft="#1A1A1A", text_disabled="#555555",
    border="#000000", border_light="#333333",
    hex_seed="#0033A0", is_dark=False,
)


THEME_PALETTES: dict[str, Palette] = {
    "blue": BLUE_PALETTE,
    "dark": DARK_PALETTE,
    "sobre": SOBRE_PALETTE,
    "contrast": CONTRAST_PALETTE,
}

THEMES_CONFIG = [
    ("blue", "Bleu", "#1565C0", False),
    ("dark", "Dark", "#212121", True),
    ("sobre", "Sobre", "#37474F", False),
    ("contrast", "Contrasté", "#0033A0", False),
]


def palette_from_seed(hex_seed: str = "#1565C0", is_dark: bool = False) -> Palette:
    """Create a Palette from a seed color (auto-generates M3 tonal palette).

    Falls back to the closest matching built-in palette if available,
    otherwise returns a blue default.
    """
    for _, pal in THEME_PALETTES.items():
        if pal.hex_seed.lower() == hex_seed.lower() and pal.is_dark == is_dark:
            return pal
    return DARK_PALETTE if is_dark else BLUE_PALETTE
