"""ArtizBoard Components — Flet M3 Widget Library (v1.0)

Composants Flet réutilisables basés sur Material Design v3 + Fibonacci.
Inspiré de LarcCommon/phibuilder/widgets pour PySide6/QSS.

Usage:
    from ArtizBoardCommon.components import button, card, textfield, kpi_card
    page.add(
        card("Mon Titre", ft.Text("Contenu"), variant="elevated"),
        button("Valider", variant="filled", icon=icons.CHECK, on_click=handle),
    )
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import flet as ft

from ArtizBoardCommon.design_system import ds
from ArtizBoardCommon.shapes import Shape, ElevationLevel


# ═══════════════════════════════════════════════════════
#  Enums — Variants M3
# ═══════════════════════════════════════════════════════

class ButtonVariant(str, Enum):
    FILLED = "filled"
    TONAL = "tonal"
    OUTLINED = "outlined"
    TEXT = "text"
    ELEVATED = "elevated"


class CardVariant(str, Enum):
    ELEVATED = "elevated"
    FILLED = "filled"
    OUTLINED = "outlined"


class FieldVariant(str, Enum):
    FILLED = "filled"
    OUTLINED = "outlined"


class Severity(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


# ═══════════════════════════════════════════════════════
#  Button
# ═══════════════════════════════════════════════════════

def button(
    text: str,
    variant: ButtonVariant = ButtonVariant.FILLED,
    icon: str = "",
    on_click: Callable = None,
    disabled: bool = False,
    width: Optional[int] = None,
    height: int = 48,
    expand: bool = False,
) -> ft.Control:
    """M3 Button — FILLED, TONAL, OUTLINED, TEXT, ELEVATED.

    Height = 48px (peut être Fibonacci 52px via ds.button_height).
    """
    height = height or ds.button_height

    if variant == ButtonVariant.FILLED:
        return ft.FilledButton(
            content=ft.Text(text),
            icon=icon or None,
            on_click=on_click,
            disabled=disabled,
            width=width,
            height=height,
            expand=expand,
        )
    elif variant == ButtonVariant.TONAL:
        return ft.FilledTonalButton(
            content=ft.Text(text),
            icon=icon or None,
            on_click=on_click,
            disabled=disabled,
            width=width,
            height=height,
            expand=expand,
        )
    elif variant == ButtonVariant.OUTLINED:
        return ft.OutlinedButton(
            content=ft.Text(text),
            icon=icon or None,
            on_click=on_click,
            disabled=disabled,
            width=width,
            height=height,
            expand=expand,
        )
    elif variant == ButtonVariant.ELEVATED:
        return ft.ElevatedButton(
            content=ft.Text(text),
            icon=icon or None,
            on_click=on_click,
            disabled=disabled,
            width=width,
            height=height,
            expand=expand,
        )
    else:  # TEXT
        return ft.TextButton(
            content=ft.Text(text),
            icon=icon or None,
            on_click=on_click,
            disabled=disabled,
            width=width,
        )


def icon_button(
    icon: str,
    on_click: Callable = None,
    tooltip: str = "",
    size: int = 0,
    variant: ButtonVariant = ButtonVariant.FILLED,
) -> ft.IconButton:
    """M3 Icon Button."""
    sz = size or ds.icon_md
    style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(ds.SHAPE_FULL.radius.top_left),
    )
    if variant == ButtonVariant.OUTLINED:
        return ft.IconButton(
            icon=icon,
            icon_size=sz,
            on_click=on_click,
            tooltip=tooltip,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(ds.SHAPE_FULL.radius.top_left),
                side=ft.BorderSide(1, ds.p.outline),
            ),
        )
    elif variant == ButtonVariant.TONAL:
        return ft.IconButton(
            icon=icon,
            icon_size=sz,
            on_click=on_click,
            tooltip=tooltip,
            style=style,
        )
    return ft.IconButton(
        icon=icon,
        icon_size=sz,
        on_click=on_click,
        tooltip=tooltip,
        style=style,
    )


# ═══════════════════════════════════════════════════════
#  Card
# ═══════════════════════════════════════════════════════

def card(
    title: str = "",
    content: ft.Control = None,
    subtitle: str = "",
    actions: list[ft.Control] = None,
    variant: CardVariant = CardVariant.ELEVATED,
    width: Optional[int] = None,
    expand: bool = False,
    on_click: Callable = None,
) -> ft.Card:
    """M3 Card — ELEVATED, FILLED, OUTLINED.

    Adapté de LarcCommon M3Card.
    """
    card_kwargs = dict(
        width=width,
        expand=expand,
        elevation=2 if variant == CardVariant.ELEVATED else 0,
        shape=ft.RoundedRectangleBorder(ds.SHAPE_MD.radius.top_left),
        margin=ft.Margin(0, 0, 0, ds.space_md),
    )

    if variant == CardVariant.FILLED:
        card_kwargs["bgcolor"] = ds.p.surface_variant
    elif variant == CardVariant.OUTLINED:
        card_kwargs["bgcolor"] = None

    card_ctrl = ft.Card(**card_kwargs)

    content_list = []

    if title or subtitle:
        title_row = []
        if title:
            title_row.append(ft.Text(
                title,
                style=ds.textstyle("title_medium"),
                color=ds.p.text_strong,
            ))
        header_items = [ft.Row(title_row, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)]
        if subtitle:
            header_items.append(ft.Text(
                subtitle,
                style=ds.textstyle("body_small"),
                color=ds.p.text_soft,
            ))
        content_list.append(
            ft.Container(
                ft.Column(header_items, spacing=ds.space_xxs),
                padding=ft.Padding(ds.space_md, ds.space_md, ds.space_md, ds.space_xs),
            )
        )

    if content is not None:
        content_list.append(
            ft.Container(
                content,
                padding=ft.Padding(ds.space_md, 0, ds.space_md, ds.space_md),
            )
        )

    if actions:
        content_list.append(
            ft.Container(
                ft.Row(actions, spacing=ds.space_xs,
                       alignment=ft.MainAxisAlignment.END),
                padding=ft.Padding(ds.space_md, 0, ds.space_md, ds.space_md),
            )
        )

    card_ctrl.content = ft.Column(content_list, spacing=0)
    if on_click:
        card_ctrl.on_click = on_click

    return card_ctrl


# ═══════════════════════════════════════════════════════
#  Text Field
# ═══════════════════════════════════════════════════════

def textfield(
    label: str = "",
    hint: str = "",
    value: str = "",
    icon: str = "",
    password: bool = False,
    multiline: bool = False,
    min_lines: int = 1,
    max_lines: int = 5,
    error: str = "",
    on_change: Callable = None,
    on_submit: Callable = None,
    prefix_icon: str = "",
    suffix_icon: str = "",
    width: Optional[int] = None,
) -> ft.TextField:
    """M3 TextField — OUTLINED, avec gestion erreur.

    Adapté de LarcCommon M3TextField.
    """
    return ft.TextField(
        label=label,
        hint_text=hint,
        value=value,
        password=password,
        can_reveal_password=password,
        multiline=multiline,
        min_lines=min_lines,
        max_lines=max_lines,
        prefix_icon=prefix_icon or None,
        suffix_icon=suffix_icon or None,
        on_change=on_change,
        on_submit=on_submit,
        width=width,
        border=ft.InputBorder.OUTLINE,
        border_radius=ds.SHAPE_XS.radius.top_left,
        text_style=ds.textstyle("body_medium"),
        label_style=ds.textstyle("body_small"),
        content_padding=ft.Padding(ds.t.field_pad_h, ds.t.field_pad_v,
                                    ds.t.field_pad_h, ds.t.field_pad_v),
        height=ds.field_height if not multiline else None,
    )


# ═══════════════════════════════════════════════════════
#  Typography labels
# ═══════════════════════════════════════════════════════

def headline(text: str, size: str = "medium") -> ft.Text:
    """M3 Headline — large, medium, small."""
    return ft.Text(text, style=ds.textstyle(f"headline_{size}"),
                   color=ds.p.text_strong)


def title(text: str, size: str = "medium") -> ft.Text:
    """M3 Title — large, medium, small."""
    return ft.Text(text, style=ds.textstyle(f"title_{size}"),
                   color=ds.p.text_strong)


def body(text: str, size: str = "medium", color: str = "") -> ft.Text:
    """M3 Body — large, medium, small."""
    return ft.Text(
        text,
        style=ds.textstyle(f"body_{size}"),
        color=color or ds.p.text_strong,
    )


def label(text: str, size: str = "medium", color: str = "") -> ft.Text:
    """M3 Label — large, medium, small."""
    return ft.Text(
        text,
        style=ds.textstyle(f"label_{size}"),
        color=color or ds.p.text_soft,
    )


def caption(text: str) -> ft.Text:
    """Small caption text."""
    return ft.Text(
        text,
        style=ds.textstyle("label_small"),
        color=ds.p.text_disabled,
    )


# ═══════════════════════════════════════════════════════
#  Section Header
# ═══════════════════════════════════════════════════════

def section_header(title_text: str, action: ft.Control = None,
                   subtitle: str = "") -> ft.Row:
    """Section header with optional action button."""
    items = [
        ft.Text(title_text, style=ds.textstyle("title_large"),
                color=ds.p.text_strong,
                expand=True),
    ]
    if action:
        items.append(action)
    return ft.Container(
        ft.Row(items, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding(0, ds.space_md, 0, ds.space_sm),
    )


# ═══════════════════════════════════════════════════════
#  KPI Card
# ═══════════════════════════════════════════════════════

def kpi_card(
    value: str,
    label_text: str,
    icon: str = "",
    color: str = "",
    trend: str = "",
) -> ft.Container:
    """Dashboard KPI card — valeur + label + icône optionnelle.

    Fibonacci : largeur = golden_width(120) ≈ 194px.
    """
    bg = color or ds.p.primary_container
    fg = ds.p.on_primary_container if color else ds.p.text_strong

    items = []
    if icon:
        items.append(ft.Icon(icon, size=ds.icon_sm, color=fg))
    items.append(ft.Text(value, style=ds.textstyle("headline_small"),
                         color=fg))
    if trend:
        trend_color = ds.p.error if trend.startswith("-") else ds.p.success
        items.append(ft.Text(trend, size=ds.typo.body_small.size,
                         color=trend_color))

    return ft.Container(
        ft.Column([
            ft.Row(items, spacing=ds.space_xs,
                   alignment=ft.MainAxisAlignment.START),
            ft.Text(label_text, style=ds.textstyle("label_small"),
                    color=fg),
        ], spacing=ds.space_xxs),
        padding=ft.Padding(ds.space_md, ds.space_md, ds.space_md, ds.space_md),
        bgcolor=bg,
        border_radius=ds.SHAPE_MD.radius.top_left,
        expand=True,
        height=ds.space_xxl,  # 84 px (Fibonacci 21 × 4)
    )


# ═══════════════════════════════════════════════════════
#  Chip
# ═══════════════════════════════════════════════════════

def chip(
    label_text: str,
    icon: str = "",
    selected: bool = False,
    on_click: Callable = None,
    color: str = "",
) -> ft.Chip:
    """M3 Chip — filtre ou label."""
    return ft.Chip(
        label=ft.Text(label_text, style=ds.textstyle("label_small")),
        leading=ft.Icon(icon, size=ds.icon_sm) if icon else None,
        selected=selected,
        on_select=lambda e: on_click(e) if on_click else None,
        bgcolor=color or ds.p.surface_variant,
        selected_color=ds.p.primary_container,
        check_color=ds.p.primary,
    )


# ═══════════════════════════════════════════════════════
#  Divider / Separator
# ═══════════════════════════════════════════════════════

def divider(height: int = 1) -> ft.Divider:
    return ft.Divider(height=height, color=ds.p.outline_variant)


def spacer(pixels: int = 0) -> ft.Container:
    """Empty spacer. Default = ds.space_md."""
    return ft.Container(height=pixels or ds.space_md)


# ═══════════════════════════════════════════════════════
#  Data Table
# ═══════════════════════════════════════════════════════

def data_table(
    columns: list[str],
    rows: list[list[str]],
    sort_column: int = 0,
    sort_ascending: bool = True,
) -> ft.DataTable:
    """M3 DataTable — tri, alternance de lignes, header fixe."""
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(col, style=ds.textstyle("label_medium"),
                                    color=ds.p.text_strong))
            for col in columns
        ],
        rows=[
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(cell, style=ds.textstyle("body_small")))
                       for cell in row],
            )
            for row in rows
        ],
        border=ft.Border(
            bottom=ft.BorderSide(1, ds.p.outline_variant),
        ),
        border_radius=ds.SHAPE_SM.radius.top_left,
        heading_row_color=ds.p.surface_variant,
        data_row_min_height=ds.t.table_row_min,
        data_row_max_height=ds.space_xxl + ds.space_xxs,  # 84 + 4 = 88 (Fibonacci)
        column_spacing=ds.space_md,
        heading_row_height=ds.t.header_height,
        sort_column_index=sort_column,
        sort_ascending=sort_ascending,
    )


# ═══════════════════════════════════════════════════════
#  Dialog / Alert
# ═══════════════════════════════════════════════════════

def dialog(
    title: str,
    content: ft.Control,
    actions: list[ft.Control] = None,
    on_dismiss: Callable = None,
) -> ft.AlertDialog:
    """M3 Dialog — titre + contenu + actions."""
    return ft.AlertDialog(
        title=ft.Text(title, style=ds.textstyle("title_medium")),
        content=content,
        actions=actions or [],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(ds.SHAPE_MD.radius.top_left),
        on_dismiss=on_dismiss,
    )


def confirm_dialog(
    title: str,
    message: str,
    on_confirm: Callable,
    on_cancel: Callable = None,
    confirm_text: str = "Confirmer",
    cancel_text: str = "Annuler",
) -> ft.AlertDialog:
    """M3 Confirmation Dialog."""
    return dialog(
        title=title,
        content=ft.Text(message, style=ds.textstyle("body_medium")),
        actions=[
            button(cancel_text, variant=ButtonVariant.TEXT,
                   on_click=lambda e: (on_cancel or (lambda: None))()),
            button(confirm_text, variant=ButtonVariant.FILLED,
                   on_click=lambda e: on_confirm()),
        ],
    )


# ═══════════════════════════════════════════════════════
#  Snackbar
# ═══════════════════════════════════════════════════════

def snackbar(
    message: str,
    severity: Severity = Severity.INFO,
    action: str = "",
    on_action: Callable = None,
    duration: int = 4000,
) -> ft.SnackBar:
    """M3 Snackbar — info, success, warning, error."""
    colors_map = {
        Severity.INFO: ds.p.primary_container,
        Severity.SUCCESS: ds.p.success,
        Severity.WARNING: ds.p.tertiary_container,
        Severity.ERROR: ds.p.error_container,
    }
    return ft.SnackBar(
        content=ft.Text(message, style=ds.textstyle("body_small"),
                         color=ds.p.text_strong),
        action=action or "OK" if not on_action else action,
        on_action=on_action,
        duration=duration,
        bgcolor=colors_map.get(severity, ds.p.surface_variant),
        shape=ft.RoundedRectangleBorder(ds.SHAPE_XS.radius.top_left),
        behavior=ft.SnackBarBehavior.FLOATING,
        margin=ft.Padding(ds.space_lg, 0, ds.space_lg, ds.space_lg),
    )


# ═══════════════════════════════════════════════════════
#  Badge
# ═══════════════════════════════════════════════════════

def badge(
    text: str,
    severity: Severity = Severity.INFO,
    size: str = "small",
) -> ft.Container:
    """M3 Badge — compteur, statut."""
    colors = {
        Severity.INFO: (ds.p.primary_container, ds.p.text_strong),
        Severity.SUCCESS: (ds.p.success, ds.p.on_primary),
        Severity.WARNING: (ds.p.tertiary_container, ds.p.text_strong),
        Severity.ERROR: (ds.p.error_container, ds.p.on_error),
    }
    bg, fg = colors.get(severity, colors[Severity.INFO])
    pad = ds.space_xs if size == "small" else ds.space_xs
    font_size = None
    return ft.Container(
        ft.Text(text, size=ds.typo.label_small.size, color=fg, weight=ft.FontWeight.BOLD),
        padding=ft.Padding(pad, 2, pad, 2),
        bgcolor=bg,
        border_radius=ds.SHAPE_FULL.radius.top_left,
    )


# ═══════════════════════════════════════════════════════
#  Empty State
# ═══════════════════════════════════════════════════════

def empty_state(
    icon: str,
    title: str,
    description: str = "",
    action: ft.Control = None,
) -> ft.Column:
    """Empty state placeholder."""
    items = [
        ft.Icon(icon, size=ds.icon_lg, color=ds.p.text_disabled),
        ft.Text(title, style=ds.textstyle("title_medium"),
                color=ds.p.text_soft),
    ]
    if description:
        items.append(ft.Text(description, style=ds.textstyle("body_small"),
                      color=ds.p.text_disabled))
    if action:
        items.append(spacer(ds.space_sm))
        items.append(action)

    return ft.Column(
        items,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=ds.space_sm,
    )


# ═══════════════════════════════════════════════════════
#  Error / Info Banner
# ═══════════════════════════════════════════════════════

def banner(
    message: str,
    severity: Severity = Severity.ERROR,
    icon: str = "",
    on_close: Callable = None,
) -> ft.Container:
    """Info/Error banner strip."""
    bg_map = {
        Severity.ERROR: ds.p.error_container,
        Severity.WARNING: ds.p.tertiary_container,
        Severity.INFO: ds.p.primary_container,
        Severity.SUCCESS: ds.p.success,
    }
    fg_map = {
        Severity.INFO: ds.p.text_strong,
        Severity.SUCCESS: ds.p.on_primary if hasattr(ds.p, 'on_primary') else white_text(ds.p.success),
        Severity.WARNING: ds.p.text_strong,
        Severity.ERROR: ds.p.on_error,
    }
    icons_map = {
        Severity.ERROR: "error",
        Severity.WARNING: "warning",
        Severity.INFO: "info",
        Severity.SUCCESS: "check_circle",
    }

    return ft.Container(
        ft.Row([
            ft.Icon(icon or icons_map.get(severity, "info"),
                    size=ds.icon_sm,
                    color=fg_map.get(severity, ds.p.text_strong)),
            ft.Text(message, style=ds.textstyle("body_small"),
                    color=fg_map.get(severity, ds.p.text_strong),
                    expand=True),
        ], spacing=ds.space_sm),
        padding=ft.Padding(ds.space_md, ds.space_sm,
                            ds.space_md, ds.space_sm),
        bgcolor=bg_map.get(severity, ds.p.surface_variant),
        border_radius=ds.SHAPE_XS.radius.top_left,
    )


def white_text(hex_color: str) -> str:
    """Helper: returns white text color for a bg."""
    # Simple heuristic — if bg is dark, return white
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return "#FFFFFF" if (r * 0.299 + g * 0.587 + b * 0.114) < 150 else "#000000"


# ═══════════════════════════════════════════════════════
#  Layout helpers
# ═══════════════════════════════════════════════════════

def container(
    content: ft.Control,
    padding: int = 0,
    bgcolor: str = "",
    border_radius: int = 0,
    expand: bool = False,
    width: int = 0,
    height: int = 0,
    alignment: ft.Alignment = None,
    border: ft.Border = None,
) -> ft.Container:
    """Styled container wrapper."""
    return ft.Container(
        content=content,
        padding=padding or ds.space_md,
        bgcolor=bgcolor or None,
        border_radius=border_radius or ds.SHAPE_MD.radius.top_left,
        expand=expand,
        width=width or None,
        height=height or None,
        alignment=alignment,
        border=border,
    )


def row(
    controls: list[ft.Control],
    spacing: int = 0,
    alignment: ft.MainAxisAlignment = None,
    vertical_alignment: ft.CrossAxisAlignment = None,
    expand: bool = False,
    wrap: bool = False,
) -> ft.Row:
    """Styled row."""
    return ft.Row(
        controls=controls,
        spacing=spacing or ds.space_sm,
        alignment=alignment or ft.MainAxisAlignment.START,
        vertical_alignment=vertical_alignment or ft.CrossAxisAlignment.CENTER,
        expand=expand,
        wrap=wrap,
    )


def column(
    controls: list[ft.Control],
    spacing: int = 0,
    alignment: ft.MainAxisAlignment = None,
    horizontal_alignment: ft.CrossAxisAlignment = None,
    expand: bool = False,
    scroll: ft.ScrollMode = None,
) -> ft.Column:
    """Styled column."""
    return ft.Column(
        controls=controls,
        spacing=spacing or ds.space_sm,
        alignment=alignment or ft.MainAxisAlignment.START,
        horizontal_alignment=horizontal_alignment or ft.CrossAxisAlignment.START,
        expand=expand,
        scroll=scroll,
    )


# ═══════════════════════════════════════════════════════
#  Responsive breakpoints
# ═══════════════════════════════════════════════════════

def responsive_columns(
    page_width: float,
    base: int = 12,
) -> int:
    """Return number of grid columns based on page width.

    Fibonacci: < 600px → 4, < 900px → 8, < 1200px → 12.
    """
    if page_width < 600:
        return 4
    elif page_width < 900:
        return 8
    return 12


def is_mobile(page_width: float) -> bool:
    return page_width < 600


def is_tablet(page_width: float) -> bool:
    return 600 <= page_width < 1024


def is_desktop(page_width: float) -> bool:
    return page_width >= 1024
