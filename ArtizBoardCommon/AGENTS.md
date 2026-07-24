# ArtizBoardCommon — Instructions pour agents IA

## Rôle
Package de Design System pour ArtizBoard (Flet).
Inspiré de LarcCommon/phibuilder (PySide6) mais adapté pour Flet.

Ne DOIT PAS dépendre d'autres modules ArtizBoard.
NE PAS modifier les singletons `ds` et `tm` sans comprendre l'impact global.

## Structure
```
ArtizBoardCommon/
├── __init__.py       # Export public : ds, tm, icons, PHI, etc.
├── config.ini        # Connexions DB, supabase, auth, sync, server
├── config_loader.py  # Chargeur config.ini (get_db_config, get_supabase_config…)
├── design_system.py  # Classe DesignSystem → singleton `ds`
├── theme.py          # ThemeManager → singleton `tm`
├── colors.py         # Palettes M3 (blue, dark, sobre, contrast)
├── typography.py     # TypeStyle → ft.TextStyle
├── shapes.py         # Shape (border radius), ElevationLevel
├── tokens.py         # DesignTokens (espacements, tailles)
├── phi.py            # PHI (1.618), Fibonacci, SpacingToken
└── icons.py          # Constantes d'icônes Material Design
```

## API publique (via `from ArtizBoardCommon import ...`)
- `ds` — DesignSystem (couleurs, espacements, shapes, golden ratio)
- `tm` — ThemeManager (changement de thème, construction ft.Theme)
- `icons` — Constantes d'icônes Material Design
- `PHI` — Nombre d'or (1.618)
- `SpacingToken` — Tokens d'espacement Fibonacci
- `TypeToken` — Tokens typo M3
- `Shape` — Énumération des formes
- `fibonacci()` — Suite de Fibonacci

## Usage typique dans une app Flet
```python
import flet as ft
from ArtizBoardCommon import ds

def main(page: ft.Page):
    ds.apply(page)

    # Couleurs
    container = ft.Container(bgcolor=ds.p.primary_container)

    # Espacement Fibonacci
    container.padding = ds.space_md

    # Typographie
    text = ft.Text("Titre", style=ds.textstyle("headline_medium"))

    # Formes
    card = ft.Container(border_radius=ds.border_radius(ds.SHAPE_MD))

    # Proportions
    large, small = ds.golden_split(page.width)
```

## Règles de modification
- ZÉRO hardcoding de valeurs dans l'UI des apps
- Toute nouvelle couleur/taille doit passer par `colors.py` ou `tokens.py`
- Ajouter un thème : 1) Palette dans `colors.py`, 2) Entrée dans `THEMES_CONFIG`, 3) Mapping dans `THEME_PALETTES`
- Les valeurs `ft.ColorScheme` dans `theme.py` doivent correspondre exactement à l'API Flet 0.86+
- Ne PAS casser la rétrocompatibilité avec les apps qui utilisent `ds.p.*`, `ds.space_*`, `ds.textstyle()`
