"""ArtizBoard Flet Wrapper (ftw.py)

Couche de compatibilité pour Flet 0.86+ : toutes les bizarreries d'API sont résolues ici.
Les apps n'importent JAMAIS flet directement — elles passent par ce module.

Usage: from ArtizBoardCommon.ftw import Row, Column, Container, Text, etc.
"""

import flet as ft
from typing import Optional, Callable


# ═══════════════════════════════════════════════════════
#  Alignment — ft.alignment.center n'existe pas en 0.86
# ═══════════════════════════════════════════════════════

ALIGN_CENTER = ft.alignment.Alignment(0, 0)
ALIGN_TOP_LEFT = ft.alignment.Alignment(-1, -1)
ALIGN_TOP_RIGHT = ft.alignment.Alignment(1, -1)
ALIGN_BOTTOM_LEFT = ft.alignment.Alignment(-1, 1)
ALIGN_BOTTOM_RIGHT = ft.alignment.Alignment(1, 1)

# ═══════════════════════════════════════════════════════
#  Layout
# ═══════════════════════════════════════════════════════

class Row(ft.Row):
    def __init__(self, controls=None, spacing=0, alignment=None, expand=False, **kw):
        super().__init__(controls=controls or [], spacing=spacing, expand=expand, **kw)

class Column(ft.Column):
    def __init__(self, controls=None, spacing=0, alignment=None, expand=False, scroll=None, **kw):
        super().__init__(controls=controls or [], spacing=spacing, expand=expand, scroll=scroll, **kw)

class Container(ft.Container):
    def __init__(self, content=None, padding=0, bgcolor=None, border_radius=None,
                 expand=False, width=None, height=None, alignment=None,
                 gradient=None, border=None, on_click=None, **kw):
        super().__init__(
            content=content, padding=padding, bgcolor=bgcolor,
            border_radius=border_radius, expand=expand, width=width,
            height=height, alignment=alignment, gradient=gradient,
            border=border, on_click=on_click, **kw,
        )

# ═══════════════════════════════════════════════════════
#  Typography
# ═══════════════════════════════════════════════════════

class Text(ft.Text):
    def __init__(self, value="", size=None, color=None, weight=None,
                 italic=False, text_align=None, font_family=None,
                 style=None, expand=False, opacity=None, **kw):
        if style:
            super().__init__(value=value, style=style, expand=expand, opacity=opacity, **kw)
        else:
            super().__init__(value=value, size=size, color=color, weight=weight,
                           italic=italic, text_align=text_align, font_family=font_family,
                           expand=expand, opacity=opacity, **kw)

# ═══════════════════════════════════════════════════════
#  Buttons — flet 0.86 utilise content=ft.Text() au lieu de text=
# ═══════════════════════════════════════════════════════

class FilledButton(ft.FilledButton):
    def __init__(self, text="", icon=None, on_click=None, disabled=False,
                 expand=False, width=None, height=None, style=None, **kw):
        super().__init__(
            content=ft.Text(text) if text else None,
            icon=icon, on_click=on_click, disabled=disabled,
            expand=expand, width=width, height=height, style=style, **kw,
        )

class OutlinedButton(ft.OutlinedButton):
    def __init__(self, text="", icon=None, on_click=None, disabled=False,
                 expand=False, width=None, height=None, **kw):
        super().__init__(
            content=ft.Text(text) if text else None,
            icon=icon, on_click=on_click, disabled=disabled,
            expand=expand, width=width, height=height, **kw,
        )

class TextButton(ft.TextButton):
    def __init__(self, text="", icon=None, on_click=None, disabled=False,
                 expand=False, width=None, **kw):
        super().__init__(
            content=ft.Text(text) if text else None,
            icon=icon, on_click=on_click, disabled=disabled,
            expand=expand, width=width, **kw,
        )

class ElevatedButton(ft.ElevatedButton):
    def __init__(self, text="", icon=None, on_click=None, disabled=False,
                 expand=False, width=None, height=None, **kw):
        super().__init__(
            content=ft.Text(text) if text else None,
            icon=icon, on_click=on_click, disabled=disabled,
            expand=expand, width=width, height=height, **kw,
        )

class FilledTonalButton(ft.FilledTonalButton):
    def __init__(self, text="", icon=None, on_click=None, disabled=False,
                 expand=False, width=None, height=None, **kw):
        super().__init__(
            content=ft.Text(text) if text else None,
            icon=icon, on_click=on_click, disabled=disabled,
            expand=expand, width=width, height=height, **kw,
        )

# ═══════════════════════════════════════════════════════
#  Icon Button
# ═══════════════════════════════════════════════════════

class IconButton(ft.IconButton):
    def __init__(self, icon=None, icon_size=None, on_click=None, tooltip=None,
                 icon_color=None, bgcolor=None, **kw):
        super().__init__(
            icon=icon, icon_size=icon_size, on_click=on_click,
            tooltip=tooltip, icon_color=icon_color, bgcolor=bgcolor, **kw,
        )

# ═══════════════════════════════════════════════════════
#  TextField
# ═══════════════════════════════════════════════════════

class TextField(ft.TextField):
    def __init__(self, label="", hint="", value="", password=False,
                 prefix_icon=None, suffix_icon=None, width=None,
                 multiline=False, min_lines=1, max_lines=1,
                 on_change=None, on_submit=None,
                 text_style=None, label_style=None,
                 border_radius=None, border=None,
                 content_padding=None, height=None, **kw):
        super().__init__(
            label=label, hint_text=hint, value=value, password=password,
            can_reveal_password=password, prefix_icon=prefix_icon,
            suffix_icon=suffix_icon, width=width, multiline=multiline,
            min_lines=min_lines, max_lines=max_lines,
            on_change=on_change, on_submit=on_submit,
            text_style=text_style, label_style=label_style,
            border_radius=border_radius, border=border or ft.InputBorder.OUTLINE,
            content_padding=content_padding, height=height, **kw,
        )

# ═══════════════════════════════════════════════════════
#  Card
# ═══════════════════════════════════════════════════════

class Card(ft.Card):
    def __init__(self, content=None, elevation=2, bgcolor=None,
                 shape=None, margin=None, expand=False, **kw):
        super().__init__(
            content=content, elevation=elevation, bgcolor=bgcolor,
            shape=shape, margin=margin, expand=expand, **kw,
        )

# ═══════════════════════════════════════════════════════
#  Dialog
# ═══════════════════════════════════════════════════════

class AlertDialog(ft.AlertDialog):
    def __init__(self, title=None, content=None, actions=None, shape=None, **kw):
        super().__init__(
            title=title, content=content, actions=actions or [],
            shape=shape, **kw,
        )

# ═══════════════════════════════════════════════════════
#  Misc
# ═══════════════════════════════════════════════════════

class Icon(ft.Icon):
    pass

class Image(ft.Image):
    def __init__(self, src="", fit=None, border_radius=None, width=None, height=None, **kw):
        super().__init__(
            src=src, fit=fit, border_radius=border_radius,
            width=width, height=height, **kw,
        )

class VerticalDivider(ft.VerticalDivider):
    pass

class Divider(ft.Divider):
    def __init__(self, height=1, color=None):
        super().__init__(height=height, color=color)

class Dropdown(ft.Dropdown):
    def __init__(self, label="", options=None, value=None, width=None,
                 hint_text=None, border_radius=None, on_change=None, **kw):
        super().__init__(
            label=label, options=options, value=value, width=width,
            hint_text=hint_text, border_radius=border_radius,
            on_change=on_change, **kw,
        )

class Checkbox(ft.Checkbox):
    def __init__(self, label="", value=False, **kw):
        super().__init__(label=label, value=value, **kw)

class Stack(ft.Stack):
    pass

class SnackBar(ft.SnackBar):
    def __init__(self, content=None, bgcolor=None, duration=4000,
                 shape=None, behavior=None, margin=None, **kw):
        super().__init__(content=content, bgcolor=bgcolor, duration=duration,
                        shape=shape, behavior=behavior, margin=margin, **kw)

# ═══════════════════════════════════════════════════════
#  Utility — mise à jour safe
# ═══════════════════════════════════════════════════════

def safe_update(control):
    """Appelle .update() sans planter si le contrôle n'est pas monté."""
    try:
        control.update()
    except RuntimeError:
        pass

# Re-export utiles
FontWeight = ft.FontWeight
TextAlign = ft.TextAlign
MainAxisAlignment = ft.MainAxisAlignment
CrossAxisAlignment = ft.CrossAxisAlignment
ScrollMode = ft.ScrollMode
Border = ft.Border
BorderSide = ft.BorderSide
Padding = ft.Padding
Margin = ft.Margin
RoundedRectangleBorder = ft.RoundedRectangleBorder
LinearGradient = ft.LinearGradient
ButtonStyle = ft.ButtonStyle
InputBorder = ft.InputBorder
ThemeMode = ft.ThemeMode
PageTheme = ft.Theme
DropdownOption = ft.dropdown.Option
Colors = ft.Colors
Icons = ft.Icons
app = ft.app
