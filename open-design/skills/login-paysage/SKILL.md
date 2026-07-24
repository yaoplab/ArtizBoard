# Skill: Login Paysage

## 0. Contexte

**Projet** : ArtizBoard
**Module** : `apps/common/login.py` — écran de connexion
**Utilisateurs** : Admin (desktop), Staff (mobile), Client (web)
**Dépendances** : [[design-system]], [[artizboard-m3]], [[flet-wrapper]]
**Prérequis** : Design System chargé (`ds.apply(page)`)


## 1. Fonction Principale

### Type : Système Fermé

```
ENTRÉE                          →  TRAITEMENT                    →  SORTIE
email, mot de passe (user)         golden_split + construction   ├─ JWT token valide
activation token (QR)              HeroPanel(62%) + LoginForm(38%)├─ User info dict
page Flet non stylée               gradient + citations          └─ Page rendue
```

## 2. Contraintes Fonctionnelles

### Tableau global

| # | Contrainte |
|---|---|
| C1 | La fenêtre login est **fixe** : `resizable=False`, `maximizable=False` |
| C2 | Les dimensions suivent le **golden ratio** : `ds.golden_width(680)` = ~1100 × 680 px |
| C3 | La fenêtre est **centrée** sur l'écran via tkinter |
| C4 | Le layout est un split **62%/38%** : HeroPanel à gauche, LoginForm à droite |
| C5 | Le HeroPanel utilise un gradient vertical primaire → container → background |
| C6 | Le LoginForm supporte l'auth email/mdp ET le QR code d'activation |
| C7 | En **mobile** (<700px), seul le LoginForm est affiché (pas de HeroPanel) |

### Sous-système A — HeroPanel

| # | Contrainte |
|---|---|
| A1 | Fond : `ds.p.primary` avec gradient `primary → primary_container → background` |
| A2 | Le nom de l'app est en `headline_large`, couleur `ds.p.on_primary` |
| A3 | La citation est affichée dans un conteneur avec fond `ds.p.primary_container` |
| A4 | Les couleurs du texte sur fond foncé sont strictement M3 natives, jamais `with_opacity()` |
| A5 | La photo de héros est optionnelle (`photo_path=""` → pas affichée) |

### Sous-système B — LoginForm

| # | Contrainte |
|---|---|
| B1 | Bouton "Mot de passe oublié" redirige (placeholder) |
| B2 | La section QR code est toujours visible sous le formulaire |
| B3 | Le champ mot de passe peut révéler le texte (`can_reveal_password`) |
| B4 | La validation est déclenchée par le bouton OU la touche Entrée (`on_submit`) |
| B5 | Les champs utilisent `textfield()` de ArtizBoardCommon, pas `ft.TextField` brut |

## 3. Code complet

### Imports obligatoires

```python
import flet as ft
import tkinter as tk
from ArtizBoardCommon import ds, tm
from ArtizBoardCommon.components import (
    button, textfield, spacer, divider,
    ButtonVariant,
)

# Icônes (ft.Icons.*)
from flet import Icons as _
# Utiliser: _.STOREFRONT, _.DARK_MODE, _.LIGHT_MODE,
#           _.LOGIN, _.QR_CODE_2, _.KEYBOARD

# Citations
QUOTES = [
    {"text": "La simplicité est la sophistication suprême.", "author": "L. de Vinci"},
    {"text": "Le succès n'est pas final, l'échec n'est pas fatal.", "author": "W. Churchill"},
    {"text": "La qualité n'est pas un acte, c'est une habitude.", "author": "Aristote"},
]
```

### Fenêtre

```python
page.window.width = int(ds.golden_width(680))  # ≈ 1100px
page.window.height = 680
page.window.resizable = False
page.window.maximizable = False
# Centrage
root = tk.Tk()
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.destroy()
page.window.left = (sw - page.window.width) // 2
page.window.top = (sh - page.window.height) // 2
```

### HeroPanel

```python
class HeroPanel(ft.Container):
    def __init__(self, photo_path=""):
        quote = QUOTES[2]
        super().__init__(
            padding=0, bgcolor=ds.p.primary, expand=True,
            alignment=ft.alignment.Alignment(0, 0),
            gradient=ft.LinearGradient(
                begin=ft.alignment.Alignment(0, 1),
                end=ft.alignment.Alignment(0, -1),
                colors=[ds.p.primary, ds.p.primary_container, ds.p.background],
            ),
            content=ft.Column([
                ft.Container(expand=True),
                ft.Container(ft.Column([
                    ft.Container(
                        ft.Icon(_.STOREFRONT, size=ds.space_xxl, color=ds.p.on_primary),
                        bgcolor=ds.p.primary_container,
                        border_radius=ds.SHAPE_FULL.radius.top_left,
                        padding=ds.space_md,
                    ),
                    spacer(ds.space_md),
                    ft.Text("ArtizBoard", style=ds.textstyle("headline_large"),
                            color=ds.p.on_primary, text_align=_.CENTER),
                    spacer(ds.space_xxs),
                    ft.Text("Systeme Commercial Hybride",
                            style=ds.textstyle("body_large"),
                            color=ds.p.primary_container, text_align=_.CENTER),
                    spacer(ds.space_lg),
                    ft.Container(
                        ft.Column([
                            ft.Text(f'"{quote["text"]}"',
                                    style=ds.textstyle("title_medium"),
                                    color=ds.p.on_primary, italic=True, text_align=_.CENTER),
                            spacer(ds.space_xs),
                            ft.Text(f"— {quote['author']}",
                                    style=ds.textstyle("body_small"),
                                    color=ds.p.primary_container, text_align=_.CENTER),
                        ]),
                        padding=ds.space_md, bgcolor=ds.p.primary_container,
                        border_radius=ds.SHAPE_LG.radius.top_left,
                    ),
                ])),
                ft.Container(expand=True),
                ft.Container(
                    ft.Text("© 2026 ArtizBoard", style=ds.textstyle("label_small"),
                            color=ds.p.surface_container_highest, text_align=_.CENTER),
                    padding=ft.Padding(0,0,0,ds.space_md),
                ),
            ]),
        )
```

### LoginForm

```python
class LoginForm(ft.Container):
    def __init__(self, on_login, on_theme_toggle, page_width=1100):
        _, form_width = ds.golden_split(page_width)
        field_w = int(form_width * 0.85)
        super().__init__(
            bgcolor=ds.p.background, expand=True,
            alignment=ft.alignment.Alignment(0,0),
            content=ft.Column([
                ft.Container(expand=True),
                ft.Container(ft.Column([
                    ft.IconButton(_.DARK_MODE if not tm.is_dark else _.LIGHT_MODE,
                                 on_click=on_theme_toggle),
                    spacer(ds.space_md),
                    ft.Row([ft.Icon(_.STOREFRONT, ds.icon_md, ds.p.primary),
                            spacer(ds.space_xs),
                            ft.Text("ArtizBoard Admin", ds.textstyle("headline_medium"))]),
                    spacer(ds.space_xxs),
                    ft.Text("Connectez-vous", ds.textstyle("body_medium"), ds.p.text_soft),
                    spacer(ds.space_md),
                    textfield("Email", prefix_icon="email", width=field_w),
                    spacer(ds.space_sm),
                    textfield("Mot de passe", password=True, prefix_icon="lock", width=field_w),
                    spacer(ds.space_sm),
                    ft.Text("", color=ds.p.error),
                    spacer(ds.space_lg),
                    button("Se connecter", ButtonVariant.FILLED, icon=_.LOGIN,
                           on_click=on_login, expand=True),
                    spacer(ds.space_xl), divider(), spacer(ds.space_md),
                    ft.Text("Ou utilisez un code d'activation",
                            ds.textstyle("body_small"), ds.p.text_soft),
                    spacer(ds.space_sm),
                    ft.Row([
                        ft.Container(ft.Icon(_.QR_CODE_2, ds.icon_md, ds.p.primary),
                                    padding=ds.space_md, bgcolor=ds.p.primary_container,
                                    border_radius=ds.SHAPE_SM.radius.top_left),
                        spacer(ds.space_sm),
                        ft.Text("Scannez le QR code\naffiche sur l'ecran admin",
                                ds.textstyle("body_small"), ds.p.text_soft),
                    ]),
                    spacer(ds.space_sm),
                    button("Saisir un code manuellement", ButtonVariant.OUTLINED,
                           icon=_.KEYBOARD, expand=True),
                ]), padding=ds.space_xl),
                ft.Container(expand=True),
                ft.Text("v0.1.0 • Admin", ds.textstyle("label_small"), ds.p.text_disabled),
            ]),
        )
```

### Assemblage

```python
hero = HeroPanel()
form = LoginForm(on_login, on_theme_toggle, page.width)

if page.width < 700:
    page.add(form)  # Mobile: formulaire seul
else:
    page.add(ft.Row([hero, ft.VerticalDivider(width=1, color=ds.p.outline_variant), form],
                     expand=True, spacing=0))
```

## 4. Deux exemples

### Exemple 1 — Login Admin (cas simple)

```python
def main(page: ft.Page):
    page.window.width = int(ds.golden_width(680))
    page.window.height = 680
    page.window.resizable = False
    page.window.center()
    ds.apply(page)
    page.bgcolor = ds.p.background

    hero = HeroPanel()
    form = LoginForm(
        on_login=lambda email, pwd: print(f"Login: {email}"),
        on_theme_toggle=lambda e: ds.switch_theme("dark") or ds.apply(page),
        page_width=page.width
    )
    page.add(ft.Row([hero, ft.VerticalDivider(1, ds.p.outline_variant), form],
                     expand=True, spacing=0))

ft.app(target=main)
```

### Exemple 2 — Intégration dans AdminApp (cas complexe)

```python
class AdminApp:
    def _show_login(self, error=""):
        self.page.window.resizable = False
        self.page.window.width = int(ds.golden_width(680))
        self.page.window.height = 680
        self.page.controls.clear()
        # Le LoginForm est intégré au flow de l'AdminApp
        hero = HeroPanel(photo_path=PHOTO_URL)
        form = LoginForm(
            on_login=self._on_login,
            on_theme_toggle=self._on_theme_toggle,
            page_width=self.page.window.width
        )
        self.page.add(ft.Row([hero, ft.VerticalDivider(1, ds.p.outline_variant), form],
                              expand=True, spacing=0))
        self.page.update()

    def _on_login(self, email, password):
        token, refresh, user_info = self.auth.login(email, password)
        self.user = user_info
        self._show_dashboard()
```

## 5. Step by Step — Implementation

| Ordre | Action | Fichier | Resultat |
|---|---|---|---|
| 1 | Créer HeroPanel avec gradient | `apps/common/login.py` | Panel gauche rendu |
| 2 | Créer LoginForm avec champs + QR | `apps/common/login.py` | Formulaire droit rendu |
| 3 | Assembler avec golden split | `apps/common/login.py` | Layout 62/38% |
| 4 | Intégrer dans l'app (Admin/Staff/Client) | `apps/*/__main__.py` | Login fonctionnel |
| 5 | Tester mobile (<700px) | Navigateur | Formulaire seul affiché |

## Checklist

- [ ] Fenêtre golden ratio (1100×680), centrée, non redimensionnable
- [ ] HeroPanel avec gradient + citation + icône
- [ ] LoginForm avec email, mot de passe, QR code
- [ ] Mobile : seul LoginForm (<700px)
- [ ] Couleurs M3 natives, pas de `with_opacity()`
- [ ] Boutons via `button()`, champs via `textfield()`
- [ ] Support `on_submit` (touche Entrée)

## Emplacement
- `apps/common/login.py` — importable par Admin, Staff, Client
