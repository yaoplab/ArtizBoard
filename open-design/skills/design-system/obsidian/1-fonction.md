---
tags:
  - skill
  - design-system
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale

### Type : Systeme Ferme

**Entrée** : Page Flet (ft.Page)
**Sortie** : Page avec thème M3 complet appliqué
**Traitement** : ds.apply(page) → injection couleurs, polices, shapes via ft.Theme


## When to apply
- Creating a new screen or dialog
- Styling any component (color, spacing, font, shape)
- Reviewing UI code for design compliance
- Adding a new theme variant

## Règle 0 — Initialisation obligatoire
```python
from ArtizBoardCommon import ds
from ArtizBoardCommon.components import button, card, textfield, kpi_card, spacer, divider

def main(page: ft.Page):
    ds.apply(page)         # Applique le thème M3 complet
    page.bgcolor = ds.p.background
    page.padding = 0
```
Sans `ds.apply(page)`, les couleurs M3 ne fonctionnent pas.

## Règle 1 — Choisir la bonne couleur (avec exemples)
```python
# Fond de carte avec titre
ft.Container(
    ft.Column([
        ft.Text("Titre", style=ds.textstyle("title_medium"), color=ds.p.text_strong),
        ft.Text("Sous-titre", style=ds.textstyle("body_small"), color=ds.p.text_soft),
    ]),
    bgcolor=ds.p.surface,                                   # Fond carte
    border_radius=ds.SHAPE_MD.radius.top_left,
    padding=ds.space_md,
)

# Message d'erreur
ft.Text("Erreur de connexion", color=ds.p.error, size=ds.typo.label_small.size)

# Élément sélectionné (sidebar, liste)
ft.Container(..., bgcolor=ds.p.primary_container)

# Bordure de séparateur
ft.Divider(height=1, color=ds.p.outline_variant)
```

## Règle 2 — Choisir le bon espacement (avec exemples)
```python
# Card padding
ft.Container(..., padding=ds.space_md)    # 20px all sides

# Row with icon + text
ft.Row([
    ft.Icon(..., size=ds.icon_sm),
    spacer(ds.space_xs),                   # 8px icon↔text
    ft.Text("Label"),
])

# Section title + body
ft.Column([
    ft.Text("Section", ...),
    spacer(ds.space_md),                   # 20px section gap
    ft.Text("Body...", ...),
])

# Dialog action buttons
ft.Row([btn_cancel, spacer(ds.space_sm), btn_save])  # 12px between buttons
```

## Règle 3 — Choisir la bonne typo (avec exemples)
```python
# Page title
ft.Text("Tableau de bord", style=ds.textstyle("headline_medium"))

# Dialog title
ft.Text("Modifier le produit", style=ds.textstyle("title_medium"))

# Card subtitle
ft.Text("Dernière modification: hier", style=ds.textstyle("body_small"),
        color=ds.p.text_soft)

# Button label (handled automatically by button() component)
button("Enregistrer", variant=ButtonVariant.FILLED)  # uses label_large internally

# Badge
ft.Container(ft.Text("3", size=ds.typo.label_small.size, ...), ...)
```

## Règle 4 — Choisir le bon rayon (avec exemples)
```python
# Text field
ft.TextField(border_radius=ds.SHAPE_XS.radius.top_left)   # 4px

# Button, chip, nav item
ft.Container(..., border_radius=ds.SHAPE_SM.radius.top_left)  # 8px

# Card, dialog, panel
ft.Container(..., border_radius=ds.SHAPE_MD.radius.top_left)  # 12px

# Pill badge
ft.Container(..., border_radius=ds.SHAPE_FULL.radius.top_left) # pill
```

## Règle 5 — Composer un layout
```python
# Two-panel landscape
w = page.width or 1100
large, small = ds.golden_split(w)  # (682, 418)
left = ft.Container(..., width=large)
right = ft.Container(..., width=small)
page.add(ft.Row([left, divider, right], expand=True))

# Sidebar + content
ft.Row([
    ft.Container(sidebar, width=260),       # Fibonacci sidebar
    ft.VerticalDivider(1, ds.p.outline_variant),
    ft.Container(content, expand=True),
])

# Card grid (3 columns)
ft.Row([card1, spacer(ds.space_md), card2, spacer(ds.space_md), card3])
```

## Règle 6 — Fenêtre login vs dashboard
```python
# Login: fixe, golden ratio, centrée
page.window.width = int(ds.golden_width(680))
page.window.height = 680
page.window.resizable = False
page.window.maximizable = False
# Center
import tkinter as tk
root = tk.Tk()
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.destroy()
page.window.left = (sw - page.window.width) // 2
page.window.top = (sh - page.window.height) // 2

# Dashboard: maximisé
page.window.maximized = True
page.window.resizable = True
page.window.maximizable = True
```

## Règle 7 — Changer de thème
```python
ds.switch_theme("dark")
ds.apply(page)    # Essential: réapplique ft.Theme après switch
```

## Règle 8 — Mise à jour safe Flet 0.86
```python
# Liste pas encore montée
try: control.update()
except RuntimeError: pass

# Liste déjà montée (event handler)
control.update()  # safe

# Dans un callback:
def on_click(e):
    err.value = "Message"; err.update()      # safe
    page.snack_bar = ...; page.update()      # safe
```

## Règle 9 — Structure standard d'un écran
```python
# Écran avec header + body + footer
ft.Column([
    ft.Container(header, padding=ds.space_md),  # Section header
    spacer(ds.space_md),
    ft.Container(body, expand=True),             # Main content
    spacer(ds.space_md),
    ft.Container(footer, padding=ds.space_md, bgcolor=ds.p.surface),  # Actions
], expand=True)

# Écran avec sidebar
ft.Row([
    ft.Container(sidebar, width=260),
    ft.VerticalDivider(1, ds.p.outline_variant),
    ft.Container(content, expand=True),
], expand=True)
```

## Règle 10 — États UI obligatoires
Tout élément interactif doit gérer :
```
Hover    → surface_variant background
Focus    → 2px primary border
Disabled → text_disabled color, reduced opacity
Empty    → icon + "Aucune donnée" + italic
Error    → error color + message clair
Success  → success color + confirmation
Loading  → ProgressBar ou Spinner
```

## 5. Step by Step — Implementation

| Ordre | Action | Fichier | Resultat |
|---|---|---|---|
| 1 | Importer ds + appliquer à la page | `main()` | Thème M3 actif |
| 2 | Utiliser ds.p.* pour toutes les couleurs | Partout | 0 hardcoding |
| 3 | Utiliser ds.space_* pour les espacements | Partout | Fibonacci respecté |
| 4 | Utiliser ds.textstyle() pour la typo | Partout | Échelle M3 |
| 5 | Utiliser ds.SHAPE_* pour les bordures | Partout | Radius cohérents |
| 6 | Vérifier checklist (10 règles) | Revue de code | Conformité M3 |

## Checklist avant livraison
- [ ] ds.apply(page) au début
- [ ] 0 couleur en dur (#XXXXXX)
- [ ] 0 pixel en dur (20, 30, 40...)
- [ ] 0 taille de police en dur (size=14)
- [ ] 0 rayon en dur (border_radius=12)
- [ ] Multi-panel = golden_split()
- [ ] Updates protégés (try/except RuntimeError)
- [ ] États hover/focus/disabled/empty/error testés