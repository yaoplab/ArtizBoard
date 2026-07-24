---
tags:
  - skill
  - artizboard-m3
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **systeme-ferme**

## 1. Fonction Principale

### Type : Systeme Ferme

**Entrée** : Composant Flet non stylé
**Sortie** : Composant M3 conforme (couleurs, espacements, typo, shapes)
**Traitement** : Appliquer ds.p.*, ds.space_*, ds.textstyle(), ds.SHAPE_*


## When to apply
- Any Flet UI creation or modification
- Any question about styling, layout, or design
- Code review of UI code
- Building admin, staff, or client interfaces

## Colors — always via ds.p
```
Bouton principal           → ds.p.primary
Texte sur bouton            → ds.p.on_primary
Fond sélectionné             → ds.p.primary_container
Fond de carte                → ds.p.surface
Fond de page                 → ds.p.background
Erreur                       → ds.p.error
Succès                       → ds.p.success
Alerte / warning             → ds.p.tertiary
Bordure standard             → ds.p.outline
Bordure légère               → ds.p.outline_variant
Texte principal              → ds.p.text_strong
Texte secondaire             → ds.p.text_soft
Texte désactivé              → ds.p.text_disabled
```

## Spacing — Fibonacci (×4px base)
```
Icon↔text                   → ds.space_xxs  (4)
Chips gap                    → ds.space_xs   (8)
Internal padding             → ds.space_sm   (12)
Section gap                  → ds.space_md   (20)
Dialog padding               → ds.space_lg   (32)
Major section                → ds.space_xl   (52)
Hero spacing                 → ds.space_xxl  (84)
```
Rule: never 5, 10, 15, 25, 30, 40... Round to nearest Fibonacci token.

## Typography — M3 scale with context
```
Titre de page (28px Bold)           → ds.textstyle("headline_medium")
Titre de section (22px Bold)        → ds.textstyle("title_large")
Titre de panneau (16px Medium)      → ds.textstyle("title_medium")
Sous-titre (14px Medium)            → ds.textstyle("title_small")
Texte long (16px Regular)           → ds.textstyle("body_large")
Texte courant (14px Regular)        → ds.textstyle("body_medium")
Légende (12px Regular)              → ds.textstyle("body_small")
Bouton (14px Medium)                → ds.textstyle("label_large")
Chip (12px Medium)                  → ds.textstyle("label_medium")
Badge/caption (11px Medium)         → ds.textstyle("label_small")
```

## Shapes — never hardcode border-radius
```
Input field             → ds.SHAPE_XS   (4px)   via ds.SHAPE_XS.radius.top_left
Button, chip, list item → ds.SHAPE_SM   (8px)   via ds.SHAPE_SM.radius.top_left
Card, dialog, panel     → ds.SHAPE_MD   (12px)  via ds.SHAPE_MD.radius.top_left
Large container         → ds.SHAPE_LG   (16px)  via ds.SHAPE_LG.radius.top_left
Pill, badge, KPI chip   → ds.SHAPE_FULL (9999px) via ds.SHAPE_FULL.radius.top_left
```

## Macro proportions
```python
# Split any space into golden ratio (62%/38%)
large, small = ds.golden_split(page.width)

# Window dimensions
w = ds.golden_width(680)   # ≈ 1100px
h = 680                    # Fibonacci base

# Sidebar width: 260px (Fibonacci 13×20)
```

## Component sizing (fixed)
```
Button height       → 48px   (Flet default, M3 touch target)
Input height        → 32px   (ds.field_height)
Table row height    → 42px   (ds.table_row_min)
KPI card height     → 84px   (ds.space_xxl)
Icon size small     → 18px   (ds.icon_sm)
Icon size medium    → 32px   (ds.icon_md)
Icon size large     → 48px   (ds.icon_lg)
```

## Elevation levels
```
Level 0 → flat (text, icons)
Level 1 → resting card (elevation=1)
Level 2 → elevated button, FAB
Level 3 → dialog, dropdown
Level 4 → drawer, side sheet
Level 5 → modal overlay
```

## Anti-patterns — FORBIDDEN (with fix)
```
❌ bgcolor="#1565C0"         → ✅ bgcolor=ds.p.primary
❌ padding=20                → ✅ padding=ds.space_md
❌ size=28                   → ✅ style=ds.textstyle("headline_medium")
❌ border_radius=12          → ✅ radius=ds.SHAPE_MD.radius.top_left
❌ ft.Colors.BLUE            → ✅ ds.p.primary
❌ ft.alignment.center        → ✅ ft.alignment.Alignment(0,0)
❌ ft.margin.only(bottom=20)  → ✅ ft.Margin(0,0,0,ds.space_md)
❌ ft.border.only(right=...)  → ✅ ft.Border(right=ft.BorderSide(1,color))
```

## Window management
```python
# Login: fixed golden ratio, non-resizable, centered
w = int(ds.golden_width(680))
h = 680
page.window.width = w; page.window.height = h
page.window.resizable = False; page.window.maximizable = False

# Dashboard: full screen
page.window.maximized = True
page.window.resizable = True; page.window.maximizable = True
```

## CRUD rules — mandatory
```python
# Delete: soft (never CASCADE)
UPDATE table SET deleted_at = NOW(), updated_by = %s
WHERE id = %s AND deleted_at IS NULL

# Update: optimistic lock
UPDATE table SET ..., version = version + 1, updated_by = %s
WHERE id = %s AND version = %s AND deleted_at IS NULL
-- if rowcount == 0 → raise ConcurrentModificationError

# Insert: UUID + audit
INSERT INTO table (id, ..., created_by, updated_by)
VALUES (str(uuid.uuid4()), ..., user_id, user_id)
```

## Initialization — every page MUST call
```python
ds.apply(page)
page.bgcolor = ds.p.background
page.padding = 0
```

## Theme switching
```python
ds.switch_theme("dark")     # Dark mode
ds.switch_theme("blue")     # Back to default
ds.switch_theme("sobre")    # Minimalist
ds.switch_theme("contrast") # High contrast
ds.apply(page)               # Re-apply after switching
```

## 5. Step by Step — Implementation

| Ordre | Action | Fichier | Resultat |
|---|---|---|---|
| 1 | ds.apply(page) dans main() | Toute app | Thème appliqué |
| 2 | Respecter Fibonacci pour les espacements | Partout | Tokens cohérents |
| 3 | Utiliser golden_split pour layouts 2 colonnes | Partout | Proportions φ |
| 4 | Fenêtre login : fixe, centrée, φ | Login | 1100×680 |
| 5 | Fenêtre dashboard : maximisée | Dashboard | Plein écran |
| 6 | Vérifier anti-patterns (❌→✅) | Revue de code | 0 erreurs |

## Checklist — 8 points before merging UI code
- [ ] `ds.apply(page)` called at start
- [ ] Zero hardcoded hex colors
- [ ] Zero arbitrary pixel values
- [ ] All typography via ds.textstyle()
- [ ] All radii via ds.SHAPE_*
- [ ] Multi-panel uses ds.golden_split()
- [ ] CRUD: soft delete + optimistic lock + UUID + audit
- [ ] Controls tests: hover, focus, disabled, empty, error states