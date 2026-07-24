"""ArtizBoard — Login Screen (Landscape, M3 + Fibonacci)

ZÉRO hardcoding. Design :
- Golden split (φ) : 62% image / 38% formulaire
- Fibonacci (1,2,3,5,8,13,21,34...) : tous les espacements, tailles, bordures
- Material Design v3 : couleurs via ds.p, typographie via ds.typo, shapes via ds.SHAPE_*

Usage: python login.py
"""

import flet as ft
from pathlib import Path

from ArtizBoardCommon import ds, PHI, PHI_INV
from ArtizBoardCommon.components import (
    button, textfield, spacer, divider, headline, title, body, label, caption,
    ButtonVariant, is_mobile,
)

# Photo du héros — déposer l'image : C:\projet\static\hero_photo.jpg (500×309 px)
PHOTO_PATH = Path(__file__).parent / "static" / "hero_photo.jpg"
PHOTO_URL = str(PHOTO_PATH) if PHOTO_PATH.exists() else ""

QUOTES = [
    {"text": "La simplicité est la sophistication suprême.", "author": "L. de Vinci"},
    {"text": "Le succès n'est pas final, l'échec n'est pas fatal : c'est le courage de continuer qui compte.", "author": "W. Churchill"},
    {"text": "La qualité n'est pas un acte, c'est une habitude.", "author": "Aristote"},
    {"text": "L'excellence est un art que l'on atteint que par l'exercice constant.", "author": "Aristote"},
    {"text": "Votre marque est ce que les gens disent de vous quand vous n'êtes pas dans la pièce.", "author": "J. Bezos"},
]


class HeroPanel(ft.Container):
    """Panneau gauche — gradient + photo + citation."""

    def __init__(self, photo_path: str = ""):
        quote = QUOTES[2]
        photo_w = 500  # Fibonacci : golden_split(680) large part ÷ φ
        photo_h = ds.golden_height(photo_w)  # 500 / 1.618 ≈ 309

        # Couleurs lisibles sur fond sombre
        txt_primary = ds.p.on_primary          # blanc pur — contraste max
        txt_secondary = ds.p.primary_container  # bleu clair — lisible
        txt_tertiary = ds.p.surface_container_highest  # très clair

        photo_block = ft.Container(
            ft.Stack([
                ft.Image(src=photo_path, width=photo_w, height=photo_h,
                         fit="cover", border_radius=ds.SHAPE_MD.radius.top_left),
                ft.Container(
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.Alignment(0, -1),
                        end=ft.alignment.Alignment(0, 1),
                        colors=["transparent", ds.p.primary],
                    ),
                    border_radius=ds.SHAPE_MD.radius.top_left,
                ),
            ]),
            width=photo_w, height=photo_h, padding=0,
        ) if photo_path else None

        content_items = [
            ft.Container(
                ft.Image(src="http://127.0.0.1:8080/uploads/logo/logo.png",
                        fit="contain", height=84,
                        error_content=ft.Icon(ft.Icons.STOREFRONT, size=ds.space_xxl,
                                             color=ds.p.on_primary)),
                bgcolor=ds.p.primary_container,
                border_radius=ds.SHAPE_FULL.radius.top_left,
                padding=ds.space_md,
                alignment=ft.alignment.Alignment(0, 0),
            ),
        ]

        if photo_block:
            content_items.append(spacer(ds.space_md))
            content_items.append(photo_block)

        content_items.extend([
            spacer(ds.space_md),
            ft.Text("ArtizBoard", style=ds.textstyle("headline_large"),
                    color=txt_primary, text_align=ft.TextAlign.CENTER),
            spacer(ds.space_xxs),
            ft.Text("Système Commercial Hybride", style=ds.textstyle("body_large"),
                    color=txt_secondary, text_align=ft.TextAlign.CENTER),
            spacer(ds.space_lg),
            ft.Container(
                ft.Column([
                    ft.Text(f'"{quote["text"]}"', style=ds.textstyle("title_medium"),
                            italic=True, color=txt_primary,
                            text_align=ft.TextAlign.CENTER),
                    spacer(ds.space_xs),
                    ft.Text(f"— {quote['author']}", style=ds.textstyle("body_small"),
                            color=txt_secondary, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=ds.space_xxs),
                padding=ds.space_md,
                bgcolor=ds.p.primary_container,
                border_radius=ds.SHAPE_LG.radius.top_left,
            ),
        ])

        super().__init__(
            padding=0,
            bgcolor=ds.p.primary,
            expand=True,
            alignment=ft.alignment.Alignment(0, 0),
            gradient=ft.LinearGradient(
                begin=ft.alignment.Alignment(0, 1),    # bas
                end=ft.alignment.Alignment(0, -1),     # haut
                colors=[ds.p.primary, ds.p.primary_container, ds.p.background],
            ),
            content=ft.Column([
                ft.Container(expand=True),
                ft.Container(
                    ft.Column(content_items,
                              alignment=ft.MainAxisAlignment.CENTER,
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=ft.Padding(ds.space_xl, 0, ds.space_xl, 0),
                ),
                ft.Container(expand=True),
                ft.Container(
                    ft.Text("© 2026 ArtizBoard  •  Boutique & Restaurant",
                            style=ds.textstyle("label_small"),
                            color=txt_tertiary,
                            text_align=ft.TextAlign.CENTER),
                    padding=ft.Padding(0, 0, 0, ds.space_md),
                ),
            ]),
        )


class LoginForm(ft.Container):
    """Panneau droit — formulaire login."""

    def __init__(self, page_width: float = 1200,
                 on_login: callable = None, on_theme_toggle: callable = None):
        super().__init__()
        self.on_login = on_login
        self.on_theme_toggle = on_theme_toggle

        # Field width via golden ratio: small part of golden_split form area
        _, form_area = ds.golden_split(int(page_width))
        field_w = int(form_area * PHI_INV)  # ~38% of form area → ~38% of 458 ≈ 174 too small
        # Better: field fills a golden proportion of the form area
        field_w = int(form_area * 0.85)  # 85% of the form width

        self.email = textfield(
            label="Email",
            hint="nom@etablissement.com",
            prefix_icon="email",
            width=field_w,
        )
        self.password = textfield(
            label="Mot de passe",
            password=True,
            prefix_icon="lock",
            width=field_w,
            on_submit=self._handle_login,
        )
        self.error_msg = ft.Text("", color=ds.p.error, size=ds.typo.label_small.size)

    def did_mount(self):
        self.build()

    def build(self):
        self.bgcolor = ds.p.background
        self.expand = True
        self.alignment = ft.alignment.Alignment(0, 0)

        self.content = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.DARK_MODE if not ds.tm.is_dark else ft.Icons.LIGHT_MODE,
                            tooltip="Changer le thème",
                            on_click=lambda e: (
                                self.on_theme_toggle(e) if self.on_theme_toggle else None
                            ),
                        ),
                    ]),
                    spacer(ds.space_md),
                    ft.Row([
                        ft.Icon(ft.Icons.STOREFRONT, size=ds.icon_md, color=ds.p.primary),
                        spacer(ds.space_xs),
                        headline("ArtizBoard", size="medium"),
                    ]),
                    spacer(ds.space_xxs),
                    body("Connectez-vous à votre espace", size="medium", color=ds.p.text_soft),
                    spacer(ds.space_md),
                    self.email,
                    spacer(ds.space_sm),
                    self.password,
                    spacer(ds.space_xxs),
                    ft.Row([
                        ft.Container(expand=True),
                        button("Mot de passe oublié ?", variant=ButtonVariant.TEXT),
                    ]),
                    spacer(ds.space_sm),
                    self.error_msg,
                    spacer(ds.space_sm),
                    button(
                        "Se connecter",
                        variant=ButtonVariant.FILLED,
                        icon=ft.Icons.LOGIN,
                        on_click=self._handle_login,
                        expand=True,
                    ),
                    spacer(ds.space_xl),
                    divider(),
                    spacer(ds.space_md),
                    body("Ou utilisez un code d'activation", size="small", color=ds.p.text_soft),
                    spacer(ds.space_sm),
                    ft.Row([
                        ft.Container(
                            ft.Icon(ft.Icons.QR_CODE_2, size=ds.icon_md, color=ds.p.primary),
                            padding=ds.space_md,
                            bgcolor=ds.p.primary_container,
                            border_radius=ds.SHAPE_SM.radius.top_left,
                            on_click=lambda e: None,
                        ),
                        spacer(ds.space_sm),
                        ft.Text(
                            "Scannez le QR code affiché\nsur l'écran administrateur",
                            style=ds.textstyle("body_small"),
                            color=ds.p.text_soft,
                        ),
                    ]),
                    spacer(ds.space_sm),
                    button(
                        "Saisir un code manuellement",
                        variant=ButtonVariant.OUTLINED,
                        icon=ft.Icons.KEYBOARD,
                        expand=True,
                    ),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=ft.Padding(ds.space_xl, ds.space_xl, ds.space_xl, ds.space_xl),
            ),
            ft.Container(expand=True),
            ft.Container(
                ft.Text(
                    "v0.1.0  •  Mode Intranet",
                    style=ds.textstyle("label_small"),
                    color=ds.p.text_disabled,
                ),
                padding=ft.Padding(0, 0, 0, ds.space_md),
            ),
        ], alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _handle_login(self, e):
        email_val = self.email.value.strip()
        password_val = self.password.value
        if not email_val:
            self.error_msg.value = "Veuillez saisir votre email"
        elif not password_val:
            self.error_msg.value = "Veuillez saisir votre mot de passe"
        else:
            self.error_msg.value = ""
            if self.on_login:
                self.on_login(email_val, password_val)
        self.error_msg.update()


class LoginScreen:
    """Assemble Hero + Form avec golden split."""

    def __init__(self, page: ft.Page):
        self.page = page
        self._build()

    def _build(self):
        self.hero = HeroPanel(photo_path=PHOTO_URL)
        self.form = LoginForm(
            page_width=self.page.width,
            on_login=self._do_login,
            on_theme_toggle=self._toggle_theme,
        )

    def _do_login(self, email, password):
        print(f"Login: {email}")

    def _toggle_theme(self, e):
        new = "dark" if not ds.tm.is_dark else "blue"
        ds.switch_theme(new)
        ds.apply(self.page)
        self._build()
        self.page.controls.clear()
        self._render()
        self.page.update()

    def _render(self):
        total_w = self.page.width or 1200
        w_hero, w_form = ds.golden_split(total_w)

        self.hero.width = w_hero
        self.form.width = w_form

        if is_mobile(total_w):
            self.page.add(self.form)
        else:
            self.page.add(
                ft.Row([
                    self.hero,
                    ft.VerticalDivider(width=ds.border_width, color=ds.p.outline_variant),
                    self.form,
                ], expand=True, spacing=0)
            )

    def show(self):
        self._render()
        self.page.update()


# ── Entry ──

def main(page: ft.Page):
    # Golden ratio window dimensions
    base_h = 680
    w = ds.golden_width(base_h)
    page.window.width = int(w)
    page.window.height = base_h
    page.window.resizable = False
    page.window.maximizable = False
    page.window.center()
    page.title = "ArtizBoard — Connexion"
    page.padding = 0
    page.bgcolor = ds.p.background

    ds.apply(page)

    screen = LoginScreen(page)
    screen.show()


if __name__ == "__main__":
    ft.app(target=main)
