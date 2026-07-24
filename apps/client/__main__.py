"""ArtizBoard — Portail Client (Flet Web)
python -m apps.client

Onglets : Accueil | Carte | À Propos | Contact
Mode soirée : QR table → ?table=T12
"""
import flet as ft, psycopg2, psycopg2.extras, uuid, sys
from pathlib import Path
from collections import OrderedDict
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ArtizBoardCommon import ds
from ArtizBoardCommon.debug import safe_handler, set_debug
from ArtizBoardCommon.config_loader import get_db_config
from ArtizBoardCommon.components import button, textfield, spacer, headline, body, ButtonVariant

db = get_db_config()

def _conn():
    return psycopg2.connect(host=db[0], port=db[1], dbname=db[2],
                            user=db[3], password=db[4], client_encoding="UTF8")

class ClientApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self._tab = 0
        self._cart = []
        self._table = ""
        self._cat_view = None
        self._page_view = 0
        self._etab = {}
        self._pages = []
        self._faqs = []
        self._prods = []
        self._by_cat = OrderedDict()
        self._cmds = []

    def run(self):
        ds.apply(self.page)
        self.page.bgcolor = ds.p.background
        self.page.padding = 0
        self.page.title = "ArtizBoard — Portail Client"
        self._detect_table()
        self._load_data()
        self._render()

    def _detect_table(self):
        import urllib.parse
        try:
            q = urllib.parse.urlparse(self.page.url or "").query
            p = urllib.parse.parse_qs(q)
            if "table" in p:
                self._table = p["table"][0]
        except Exception:
            pass

    def _load_data(self):
        try:
            conn = _conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute("SELECT * FROM etablissements WHERE deleted_at IS NULL LIMIT 1")
            e = cur.fetchone()
            if e:
                self._etab = dict(e)

            cur.execute("""
                SELECT * FROM pages_etablissement
                WHERE etablissement_id=%s AND deleted_at IS NULL AND est_active=TRUE
                ORDER BY ordre, numero_page
            """, (self._etab.get("id", ""),))
            self._pages = [dict(r) for r in cur.fetchall()]

            cur.execute("""
                SELECT * FROM faqs
                WHERE etablissement_id=%s AND deleted_at IS NULL
                ORDER BY ordre
            """, (self._etab.get("id", ""),))
            self._faqs = [dict(r) for r in cur.fetchall()]

            cur.execute("""
                SELECT c.id AS cat_id, c.nom AS cat_nom, p.*
                FROM categories c
                JOIN produits p ON p.categorie_id = c.id
                WHERE p.etablissement_id=%s AND p.deleted_at IS NULL
                AND c.deleted_at IS NULL AND p.permets_commande=TRUE
                ORDER BY c.nom, p.nom
            """, (self._etab.get("id", ""),))
            self._prods = [dict(r) for r in cur.fetchall()]
            for r in self._prods:
                k = (r["cat_id"], r["cat_nom"])
                if k not in self._by_cat:
                    self._by_cat[k] = []
                self._by_cat[k].append(r)

            cur.execute("""
                SELECT c.id, c.reference_client, c.total, c.statut, c.statut_paiement,
                       c.created_at, c.type_service
                FROM commandes c
                WHERE c.etablissement_id=%s AND c.deleted_at IS NULL
                ORDER BY c.created_at DESC LIMIT 10
            """, (self._etab.get("id", ""),))
            self._cmds = [dict(r) for r in cur.fetchall()]

            cur.close(); conn.close()
        except Exception as e:
            print(f"[client] Load error: {e}")

    def _render(self):
        self.page.controls.clear()
        nav = self._build_nav()
        content = self._build_content()
        cart_bar = self._build_cart_bar() if self._tab == 1 else None
        items = [nav, content]
        if cart_bar:
            items.append(cart_bar)
        items.append(ft.Container(
            ft.Text("© 2026 ArtizBoard · Licence MIT", size=9, color=ds.p.text_disabled,
                    text_align=ft.TextAlign.CENTER),
            padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
        ))
        self.page.add(*items)
        self.page.update()

    # ═══════════ NAVIGATION ═══════════

    def _build_nav(self):
        tabs = [
            (0, "Accueil", ft.Icons.HOME),
            (1, "Carte", ft.Icons.RESTAURANT_MENU),
            (2, "À Propos", ft.Icons.INFO),
            (3, "Contact", ft.Icons.CONTACT_PHONE),
        ]
        cart_count = sum(c["qty"] for c in self._cart)
        row = ft.Row(spacing=0)
        for idx, lbl, ico in tabs:
            sel = self._tab == idx
            row.controls.append(
                ft.Container(
                    ft.Column([
                        ft.Icon(ico, size=22, color=ds.p.primary if sel else ds.p.text_soft),
                        ft.Text(lbl, size=10, color=ds.p.primary if sel else ds.p.text_soft,
                                weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
                    expand=True, alignment=ft.alignment.Alignment(0, 0),
                    border=ft.Border(bottom=ft.BorderSide(2, ds.p.primary if sel else ft.Colors.TRANSPARENT)),
                    on_click=safe_handler(lambda e, i=idx: self._switch_tab(i), "Client.nav.switch_tab"),
                )
            )
        if cart_count > 0:
            row.controls.append(
                ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.SHOPPING_CART, size=18, color=ds.p.primary),
                        ft.Text(str(cart_count), size=12, weight=ft.FontWeight.BOLD, color=ds.p.primary),
                    ]),
                    padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
                    on_click=safe_handler(lambda e: self._show_cart_dialog(), "Client.nav.cart_dialog"),
                )
            )
        return ft.Container(row, bgcolor=ds.p.surface,
                            border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)))

    def _switch_tab(self, idx):
        self._tab = idx
        self._cat_view = None
        self._page_view = 0
        self._render()

    # ═══════════ CONTENT ═══════════

    def _build_content(self):
        if self._tab == 0:
            return self._accueil_view()
        elif self._tab == 1:
            return self._carte_view()
        elif self._tab == 2:
            return self._apropos_view()
        else:
            return self._contact_view()

    # ═══════════ TAB 0 — ACCUEIL ═══════════

    def _accueil_view(self):
        nom = self._etab.get("nom", "Notre Établissement")
        desc = self._etab.get("historique", "Bienvenue sur notre portail.")
        mission = self._etab.get("mission", "")

        return ft.Column([
            # Hero
            ft.Container(
                ft.Column([
                    ft.Text(nom, style=ds.textstyle("headline_large"),
                            color=ds.p.on_primary, text_align=ft.TextAlign.CENTER),
                    spacer(ds.space_sm),
                    ft.Text(desc[:200], style=ds.textstyle("body_large"),
                            color=ds.p.primary_container, text_align=ft.TextAlign.CENTER),
                    spacer(ds.space_md) if self._table else ft.Container(),
                    button(f"🗺 Table {self._table} — Commander" if self._table
                           else "Voir la carte", variant=ButtonVariant.ELEVATED,
                           icon=ft.Icons.RESTAURANT_MENU,
                           on_click=safe_handler(lambda e: self._switch_tab(1), "Client.accueil.go_to_carte")),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ds.space_xl,
                bgcolor=ds.p.primary,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.Alignment(0, -1),
                    end=ft.alignment.Alignment(0, 1),
                    colors=[ds.p.primary, ds.p.primary_container],
                ),
            ),
            # Mission
            ft.Container(
                ft.Column([
                    ft.Text("Notre Mission", style=ds.textstyle("title_medium"),
                            color=ds.p.text_strong),
                    spacer(ds.space_xs),
                    ft.Text(mission or "Offrir une expérience culinaire exceptionnelle.",
                            style=ds.textstyle("body_medium"), color=ds.p.text_soft),
                ]),
                padding=ds.space_lg,
            ),
            # Quick categories
            ft.Container(
                ft.Column([
                    ft.Text("Nos catégories", style=ds.textstyle("title_medium"),
                            color=ds.p.text_strong),
                    spacer(ds.space_sm),
                    ft.Row(wrap=True, spacing=ds.space_sm,
                           controls=[self._cat_chip(cn) for (cid, cn), prods
                                    in list(self._by_cat.items())[:6]]),
                ]),
                padding=ft.Padding(ds.space_lg, 0, ds.space_lg, ds.space_lg),
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def _cat_chip(self, nom):
        return ft.Container(
            ft.Text(nom, size=13, color=ds.p.primary, weight=ft.FontWeight.BOLD),
            padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
            border=ft.Border.all(1, ds.p.primary),
            border_radius=ds.SHAPE_FULL.radius.top_left,
            on_click=safe_handler(lambda e: (setattr(self, '_tab', 1) or setattr(self, '_cat_view', None)
                                or self._render()), "Client.accueil.cat_chip"),
        )

    # ═══════════ TAB 1 — CARTE (catalogue) ═══════════

    def _carte_view(self):
        content = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        content.controls.append(
            ft.Container(
                ft.Text("Notre Carte", style=ds.textstyle("headline_small"),
                        color=ds.p.text_strong),
                padding=ft.Padding(ds.space_lg, ds.space_md, ds.space_lg, ds.space_sm),
            )
        )

        if not self._cat_view:
            for (cid, cn), prods in self._by_cat.items():
                content.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Column([
                                ft.Text(cn, style=ds.textstyle("title_medium")),
                                ft.Text(f"{len(prods)} plats", size=11, color=ds.p.text_soft),
                            ], spacing=0, expand=True),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=20, color=ds.p.primary),
                        ]),
                        padding=ft.Padding(ds.space_lg, ds.space_md, ds.space_lg, ds.space_md),
                        border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)),
                        on_click=safe_handler(lambda e, cid=cid, cn=cn: self._open_cat(cid, cn), "Client.carte.open_cat"),
                    )
                )
        else:
            cid, cn = self._cat_view
            prods = self._by_cat.get((cid, cn), [])
            content.controls.append(
                ft.Container(
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_size=20,
                                      on_click=safe_handler(lambda e: setattr(self, '_cat_view', None)
                                      or self._render(), "Client.carte.back_cat")),
                        ft.Text(cn, style=ds.textstyle("title_small"), expand=True),
                    ]),
                    padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
                    border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)),
                )
            )
            for p in prods:
                pid = str(p["id"])
                qty = next((c["qty"] for c in self._cart if c["id"] == pid), 0)
                content.controls.append(self._build_prod_row(p, qty))

        return content

    def _build_prod_row(self, p, qty):
        pid = str(p["id"])
        return ft.Container(
            ft.Row([
                ft.Container(
                    ft.Icon(ft.Icons.RESTAURANT, size=28, color=ds.p.primary_container),
                    width=56, height=56,
                    bgcolor=ds.p.surface_variant,
                    border_radius=ds.SHAPE_SM.radius.top_left,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                spacer(ds.space_sm),
                ft.Column([
                    ft.Text(p["nom"], style=ds.textstyle("body_large"),
                            weight=ft.FontWeight.BOLD),
                    ft.Text(f"{float(p['prix']):,.0f} FCFA",
                            style=ds.textstyle("title_small"), color=ds.p.primary),
                ], spacing=2, expand=True),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.REMOVE, icon_size=18,
                                  on_click=safe_handler(lambda e, pp=p: self._cart_rem(pp), "Client.carte.cart_rem"))
                    if qty > 0 else ft.Container(width=36, height=36),
                    ft.Text(str(qty) if qty > 0 else "", size=16,
                            weight=ft.FontWeight.BOLD, color=ds.p.primary),
                    ft.IconButton(icon=ft.Icons.ADD, icon_size=18,
                                  on_click=safe_handler(lambda e, pp=p: self._cart_add(pp), "Client.carte.cart_add")),
                ]),
            ]),
            padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
            bgcolor=ds.p.primary_container if qty > 0 else None,
            border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)),
        )

    def _open_cat(self, cid, cn):
        self._cat_view = (cid, cn); self._render()

    def _cart_add(self, prod):
        pid = str(prod["id"])
        ex = next((c for c in self._cart if c["id"] == pid), None)
        if ex: ex["qty"] += 1
        else: self._cart.append({"id": pid, "nom": prod["nom"], "prix": float(prod["prix"]), "qty": 1})
        self._render()

    def _cart_rem(self, prod):
        pid = str(prod["id"])
        ex = next((c for c in self._cart if c["id"] == pid), None)
        if ex:
            ex["qty"] -= 1
            if ex["qty"] <= 0: self._cart = [c for c in self._cart if c["id"] != pid]
        self._render()

    def _build_cart_bar(self):
        total = sum(c["prix"] * c["qty"] for c in self._cart)
        count = sum(c["qty"] for c in self._cart)
        if count == 0:
            return None
        return ft.Container(
            ft.Row([
                ft.Icon(ft.Icons.SHOPPING_CART, size=18, color=ds.p.primary),
                spacer(ds.space_xs),
                ft.Text(f"{count} art. • {total:,.0f} FCFA",
                        style=ds.textstyle("body_medium"), expand=True,
                        weight=ft.FontWeight.BOLD),
                button("Commander", variant=ButtonVariant.FILLED,
                       icon=ft.Icons.CHECK, on_click=safe_handler(lambda e: self._checkout(), "Client.carte.checkout"),
                       height=40),
            ]),
            padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
            bgcolor=ds.p.surface,
            border=ft.Border(top=ft.BorderSide(1, ds.p.outline_variant)),
        )

    def _show_cart_dialog(self):
        total = sum(c["prix"] * c["qty"] for c in self._cart)
        count = sum(c["qty"] for c in self._cart)
        items = ft.Column(spacing=ds.space_sm, height=300, scroll=ft.ScrollMode.AUTO)
        for c in self._cart:
            items.controls.append(
                ft.Row([
                    ft.Text(f"{c['qty']}× {c['nom']}", style=ds.textstyle("body_medium"), expand=True),
                    ft.Text(f"{c['prix']*c['qty']:,.0f} F", style=ds.textstyle("body_medium")),
                ])
            )
        dlg = ft.AlertDialog(
            title=ft.Text(f"Panier ({count} art.)", style=ds.textstyle("title_medium")),
            content=ft.Column([
                items,
                spacer(ds.space_sm),
                ft.Row([
                    ft.Text("Total:", style=ds.textstyle("title_small")),
                    ft.Container(expand=True),
                    ft.Text(f"{total:,.0f} FCFA", style=ds.textstyle("title_small"), color=ds.p.primary),
                ]),
            ], width=320),
            actions=[
                ft.TextButton("Fermer", on_click=safe_handler(lambda e: setattr(dlg, 'open', False) or self.page.update(), "Client.dialog.close")),
                ft.FilledButton("Commander", icon=ft.Icons.CHECK,
                               on_click=safe_handler(lambda e: (setattr(dlg, 'open', False), self._checkout()), "Client.dialog.checkout")),
            ],
            shape=ft.RoundedRectangleBorder(ds.SHAPE_MD.radius.top_left),
        )
        self.page.show_dialog(dlg)

    def _checkout(self):
        if not self._cart:
            self._show_snack("Panier vide"); return
        total = sum(c["prix"] * c["qty"] for c in self._cart)
        try:
            conn = _conn(); cur = conn.cursor()
            eid = self._etab.get("id")
            ref = self._table or "Client Web"
            cid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO commandes (id, etablissement_id, reference_client,
                    statut, type_service, total, statut_paiement, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (cid, eid, ref, "en_attente", "sur_place", total,
                  "en_attente", cid))
            for c in self._cart:
                cur.execute("""INSERT INTO lignes_commande
                    (id, commande_id, produit_id, quantite, prix_unitaire)
                    VALUES (%s,%s,%s,%s,%s)""",
                    (str(uuid.uuid4()), cid, c["id"], c["qty"], c["prix"]))
            conn.commit(); cur.close(); conn.close()
            self._cart = []
            self._show_snack(f"Commande #{cid[:8]} enregistrée ✓")
            self._render()
        except Exception as ex:
            self._show_snack(f"Erreur: {ex}")

    def _show_snack(self, msg):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
        self.page.update()

    # ═══════════ TAB 2 — À PROPOS ═══════════

    def _apropos_view(self):
        content = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

        has_tabs = len(self._pages) > 1
        if has_tabs:
            tab_row = ft.Row(spacing=0, scroll=ft.ScrollMode.AUTO)
            for i, p in enumerate(self._pages):
                sel = i == self._page_view
                tab_row.controls.append(
                    ft.Container(
                        ft.Text(p.get("titre", f"Page {i+1}"), size=12,
                                color=ds.p.primary if sel else ds.p.text_soft,
                                weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL,
                                text_align=ft.TextAlign.CENTER),
                        padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
                        expand=True,
                        border=ft.Border(bottom=ft.BorderSide(2, ds.p.primary if sel else ft.Colors.TRANSPARENT)),
                        on_click=safe_handler(lambda e, i=i: self._switch_page(i), "Client.apropos.switch_page"),
                    )
                )
            content.controls.append(
                ft.Container(tab_row, bgcolor=ds.p.surface,
                            border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)))
            )

        if self._pages:
            p = self._pages[self._page_view]
            content.controls.append(
                ft.Container(
                    ft.Column([
                        ft.Text(p.get("titre", ""), style=ds.textstyle("headline_small"),
                                color=ds.p.text_strong),
                        spacer(ds.space_sm),
                        self._html_block(p.get("contenu_html", "")),
                    ]),
                    padding=ds.space_lg,
                )
            )
        else:
            h = self._etab.get("historique", "")
            m = self._etab.get("mission", "")
            content.controls.append(
                ft.Container(
                    ft.Column([
                        ft.Text("À Propos", style=ds.textstyle("headline_small")),
                        spacer(ds.space_sm),
                        ft.Text(h, style=ds.textstyle("body_medium"), color=ds.p.text_soft),
                        spacer(ds.space_lg) if m else ft.Container(),
                        ft.Text("Notre Mission", style=ds.textstyle("title_medium"),
                                weight=ft.FontWeight.BOLD) if m else ft.Container(),
                        ft.Text(m, style=ds.textstyle("body_medium"), color=ds.p.text_soft),
                    ]),
                    padding=ds.space_lg,
                )
            )

        # FAQ
        if self._faqs:
            content.controls.append(
                ft.Container(
                    ft.Column([
                        ft.Text("Questions fréquentes", style=ds.textstyle("title_medium")),
                        spacer(ds.space_sm),
                        *[self._faq_card(f) for f in self._faqs],
                    ]),
                    padding=ds.space_lg,
                    bgcolor=ds.p.surface_variant,
                )
            )

        # Recent orders
        if self._cmds:
            content.controls.append(
                ft.Container(
                    ft.Column([
                        ft.Text("Commandes récentes", style=ds.textstyle("title_medium")),
                        spacer(ds.space_sm),
                        *[self._cmd_card(c) for c in self._cmds[:5]],
                    ]),
                    padding=ds.space_lg,
                )
            )

        return content

    def _switch_page(self, i):
        self._page_view = i; self._render()

    def _html_block(self, html_text):
        if not html_text:
            return ft.Text("", visible=False)
        import re
        blocks = []
        # Extract and process sections
        text = html_text

        # Container blocks with specific classes (ordered by specificity)
        containers = [
            ("hero-banner", r'<div class="hero-banner">(.*?)</div>'),
            ("stats", r'<div class="stats">(.*?)</div>'),
            ("features", r'<div class="features">(.*?)</div>'),
            ("gallery", r'<div class="gallery">(.*?)</div>'),
            ("shop-gallery", r'<div class="shop-gallery">(.*?)</div>'),
            ("contact-grid", r'<div class="contact-grid">(.*?)</div>'),
            ("logos", r'<div class="logos">(.*?)</div>'),
            ("cta-contact", r'<div class="cta-contact">(.*?)</div>'),
            ("gallery-item", r'<div class="gallery-item">(.*?)</div>'),
            ("feature", r'<div class="feature">(.*?)</div>'),
            ("shop-item", r'<div class="shop-item">(.*?)</div>'),
            ("stat", r'<div class="stat">(.*?)</div>'),
            ("contact-card", r'<div class="contact-card">(.*?)</div>'),
            ("shop-info", r'<div class="shop-info">(.*?)</div>'),
        ]

        def extract_text(t):
            t = re.sub(r'<[^>]+>', '', t).strip()
            t = t.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            t = t.replace('&#39;', "'").replace('&quot;', '"')
            return t

        def extract_img(t):
            m = re.search(r'<img[^>]+src="([^"]+)"', t)
            return m.group(1) if m else None

        def extract_attrs(t, tag):
            texts = re.findall(f'<{tag}[^>]*>(.*?)</{tag}>', t, re.DOTALL)
            return [extract_text(tx) for tx in texts]

        def process_gallery(text):
            items = re.findall(r'<div class="gallery-item">(.*?)</div>', text, re.DOTALL)
            cols = []
            for item in items[:6]:
                img_url = extract_img(item)
                cap = extract_text(item)
                cols.append(
                    ft.Container(
                        ft.Column([
                            ft.Container(
                                ft.Image(src=img_url, fit="cover",
                                         border_radius=ft.border_radius.all(8)),
                                height=140, border_radius=ft.border_radius.all(8),
                                bgcolor=ds.p.surface_variant,
                            ) if img_url else ft.Container(
                                ft.Icon(ft.Icons.IMAGE, size=40, color=ds.p.text_disabled),
                                height=140, bgcolor=ds.p.surface_variant,
                                border_radius=ft.border_radius.all(8),
                                alignment=ft.alignment.Alignment(0, 0),
                            ),
                            spacer(ds.space_xs),
                            ft.Text(cap, size=12, color=ds.p.text_soft,
                                    text_align=ft.TextAlign.CENTER),
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=160,
                    )
                )
            return ft.Container(
                ft.Row(cols, scroll=ft.ScrollMode.AUTO, spacing=ds.space_sm),
                margin=ft.Margin(0, ds.space_md, 0, ds.space_md),
            )

        def process_features(text):
            items = re.findall(r'<div class="feature">(.*?)</div>', text, re.DOTALL)
            cols = []
            for item in items:
                icon = re.search(r'<span class="icon">(.*?)</span>', item)
                icon_txt = icon.group(1) if icon else ""
                h3s = extract_attrs(item, 'h3')
                ps = extract_attrs(item, 'p')
                cols.append(
                    ft.Container(
                        ft.Column([
                            ft.Text(icon_txt, size=32, text_align=ft.TextAlign.CENTER),
                            spacer(ds.space_xs),
                            ft.Text(h3s[0] if h3s else "",
                                    style=ds.textstyle("title_small"),
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text(ps[0] if ps else "", size=13,
                                    color=ds.p.text_soft,
                                    text_align=ft.TextAlign.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ds.space_md,
                        bgcolor=ds.p.surface,
                        border_radius=ds.SHAPE_SM.radius.top_left,
                        expand=True,
                    )
                )
            return ft.Container(
                ft.Column([
                    ft.Row(cols, wrap=True, spacing=ds.space_sm),
                ]),
                margin=ft.Margin(0, ds.space_md, 0, ds.space_md),
            )

        def process_stats(text):
            items = re.findall(r'<div class="stat">(.*?)</div>', text, re.DOTALL)
            cols = []
            for item in items:
                num = extract_attrs(item, 'span')[0] if extract_attrs(item, 'span') else ""
                lbl = extract_attrs(item, 'span')[1] if len(extract_attrs(item, 'span')) > 1 else ""
                cols.append(
                    ft.Container(
                        ft.Column([
                            ft.Text(num, style=ds.textstyle("headline_medium"),
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text(lbl, size=13, color=ft.Colors.WHITE,
                                    text_align=ft.TextAlign.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                    )
                )
            return ft.Container(
                ft.Row(cols, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                padding=ds.space_lg, margin=ft.Margin(0, ds.space_md, 0, ds.space_md),
                bgcolor=ds.p.primary,
                border_radius=ds.SHAPE_MD.radius.top_left,
            )

        def process_contact_grid(text):
            items = re.findall(r'<div class="contact-card">(.*?)</div>', text, re.DOTALL)
            cols = []
            for item in items:
                icon = re.search(r'<div class="card-icon">(.*?)</div>', item)
                icon_txt = icon.group(1) if icon else ""
                h3s = extract_attrs(item, 'h3')
                ps = extract_attrs(item, 'p')
                lines = ps[0].split("<br>") if ps else []
                lines = [l.strip() for l in lines if l.strip()]
                cols.append(
                    ft.Container(
                        ft.Column([
                            ft.Text(icon_txt, size=28, text_align=ft.TextAlign.CENTER),
                            ft.Text(h3s[0] if h3s else "",
                                    style=ds.textstyle("title_small"),
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER),
                            *[ft.Text(l, size=12, color=ds.p.text_soft,
                                      text_align=ft.TextAlign.CENTER) for l in lines],
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ds.space_md, bgcolor=ds.p.surface,
                        border_radius=ds.SHAPE_SM.radius.top_left,
                        expand=True,
                    )
                )
            return ft.Container(
                ft.Row(cols, wrap=True, spacing=ds.space_sm),
                margin=ft.Margin(0, ds.space_md, 0, ds.space_md),
            )

        def process_shop_gallery(text):
            items = re.findall(r'<div class="shop-item">(.*?)</div>', text, re.DOTALL)
            cols = []
            for item in items:
                img_url = extract_img(item)
                info = re.search(r'<div class="shop-info">(.*?)</div>', item, re.DOTALL)
                h3 = extract_attrs(info.group(1) if info else '', 'h3')
                ps = extract_attrs(info.group(1) if info else '', 'p')
                cols.append(
                    ft.Container(
                        ft.Column([
                            ft.Container(
                                ft.Image(src=img_url, fit="cover",
                                         border_radius=ft.border_radius.all(8)),
                                height=160, border_radius=ft.border_radius.all(8),
                                bgcolor=ds.p.surface_variant,
                            ) if img_url else ft.Container(height=100),
                            spacer(ds.space_xs),
                            ft.Text(h3[0] if h3 else "", style=ds.textstyle("title_small"),
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(ps[0] if ps else "", size=12, color=ds.p.text_soft),
                        ]),
                        width=180, padding=ds.space_sm, bgcolor=ds.p.surface,
                        border_radius=ds.SHAPE_SM.radius.top_left,
                    )
                )
            return ft.Container(
                ft.Row(cols, scroll=ft.ScrollMode.AUTO, spacing=ds.space_sm),
                margin=ft.Margin(0, ds.space_md, 0, ds.space_md),
            )

        def process_logos(text):
            items = re.findall(r'<span class="logo-item">(.*?)</span>', text, re.DOTALL)
            chips = [ft.Container(
                ft.Text(extract_text(i), size=13, color=ds.p.primary),
                padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
                border=ft.Border.all(1, ds.p.primary),
                border_radius=ds.SHAPE_FULL.radius.top_left,
            ) for i in items]
            return ft.Container(
                ft.Row(chips, wrap=True, spacing=ds.space_sm),
                margin=ft.Margin(0, ds.space_md, 0, ds.space_md),
            )

        def process_cta(text):
            h3s = extract_attrs(text, 'h3')
            ps = extract_attrs(text, 'p')
            strongs = re.findall(r'<strong>(.*?)</strong>', text)
            lines = []
            for p in ps:
                for s in strongs:
                    p = p.replace(f'<strong>{s}</strong>', s)
                lines.append(p)
            return ft.Container(
                ft.Column([
                    ft.Text(h3s[0] if h3s else "", style=ds.textstyle("title_small"),
                            weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    *[ft.Text(l, size=13, color=ft.Colors.WHITE) for l in lines if l.strip()],
                ]),
                padding=ds.space_lg, margin=ft.Margin(0, ds.space_md, 0, ds.space_md),
                bgcolor=ds.p.primary,
                border_radius=ds.SHAPE_MD.radius.top_left,
            )

        def process_hero(text):
            h1s = extract_attrs(text, 'h1')
            ps = extract_attrs(text, 'p')
            return ft.Container(
                ft.Column([
                    (ft.Text(h1s[0], style=ds.textstyle("headline_small"),
                             color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
                     if h1s else ft.Container()),
                    (ft.Text(ps[0], color=ft.Colors.WHITE, opacity=0.85,
                             text_align=ft.TextAlign.CENTER)
                     if ps else ft.Container()),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ds.space_lg, margin=ft.Margin(0, ds.space_md, 0, ds.space_md),
                bgcolor=ds.p.primary_container,
                border_radius=ds.SHAPE_MD.radius.top_left,
            )

        def process_list(text):
            items = re.findall(r'<li>(.*?)</li>', text, re.DOTALL)
            return ft.Column([
                ft.Row([
                    ft.Text("•", size=16, color=ds.p.primary),
                    spacer(ds.space_sm),
                    ft.Text(extract_text(i).replace("<br>", ""),
                            style=ds.textstyle("body_small"), expand=True),
                ]) for i in items
            ])

        def process_paragraph(text):
            txt = extract_text(text)
            if not txt:
                return None
            classes = re.findall(r'class="([^"]+)"', text)
            is_cta = any("cta" in c for c in classes)
            is_note = any("note" in c for c in classes)
            is_signature = any("signature" in c for c in classes)
            if is_cta:
                return ft.Container(
                    ft.Text(txt, style=ds.textstyle("title_small"), color=ds.p.primary,
                            weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    padding=ds.space_md, margin=ft.Margin(0, ds.space_md, 0, 0),
                )
            return ft.Text(txt, style=ds.textstyle("body_medium"), color=ds.p.text_soft)

        # Process known containers in order
        for cname, cpattern in containers:
            def replacer(m, cn=cname):
                nonlocal blocks
                content = m.group(1)
                if cn == "gallery":
                    blocks.append(process_gallery(content))
                elif cn == "shop-gallery":
                    blocks.append(process_shop_gallery(content))
                elif cn == "features":
                    blocks.append(process_features(content))
                elif cn == "stats":
                    blocks.append(process_stats(content))
                elif cn == "contact-grid":
                    blocks.append(process_contact_grid(content))
                elif cn == "logos":
                    blocks.append(process_logos(content))
                elif cn == "cta-contact":
                    blocks.append(process_cta(content))
                elif cn == "hero-banner":
                    blocks.append(process_hero(content))
                return ""
            text = re.sub(cpattern, replacer, text, flags=re.DOTALL)

        # Process remaining inline elements
        # Headings
        for tag, style_name, size in [("h2", "title_large", None), ("h3", "title_medium", None)]:
            def h_replacer(m, sn=style_name):
                nonlocal blocks
                txt = extract_text(m.group(1))
                if txt:
                    blocks.append(
                        ft.Container(
                            ft.Text(txt, style=ds.textstyle(sn),
                                    weight=ft.FontWeight.BOLD,
                                    color=ds.p.text_strong),
                            margin=ft.Margin(0, ds.space_md, 0, ds.space_xxs),
                        )
                    )
                return ""
            text = re.sub(f'<{tag}[^>]*>(.*?)</{tag}>', h_replacer, text, flags=re.DOTALL)

        # Lists
        list_re = re.compile(r'<ul[^>]*>(.*?)</ul>', re.DOTALL)
        text = list_re.sub(lambda m: "", text)  # Remove the ul wrapper, li handled below
        li_re = re.compile(r'<li>(.*?)</li>', re.DOTALL)
        li_items = li_re.findall(text)
        if li_items:
            blocks.append(process_list(text))

        # Images standalone
        img_re = re.compile(r'<img[^>]+src="([^"]+)"[^>]*>')
        text = img_re.sub(lambda m: "", text)

        # Paragraphs and remaining text
        para_re = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL)
        for m in para_re.finditer(text):
            result = process_paragraph(m.group(0))
            if result is not None:
                blocks.append(result)
            text = text.replace(m.group(0), "")

        # Remaining text fragments
        leftover = extract_text(text)
        if leftover:
            blocks.append(ft.Text(leftover, style=ds.textstyle("body_medium"),
                                   color=ds.p.text_soft))

        return ft.Column(blocks, spacing=ds.space_sm) if blocks else ft.Text("", visible=False)

    def _faq_card(self, f):
        return ft.Container(
            ft.Column([
                ft.Text(f.get("question", "?"), style=ds.textstyle("body_medium"),
                        weight=ft.FontWeight.BOLD, color=ds.p.text_strong),
                spacer(ds.space_xxs),
                ft.Text(f.get("reponse", ""), style=ds.textstyle("body_small"),
                        color=ds.p.text_soft),
            ]),
            padding=ds.space_md, bgcolor=ds.p.surface,
            border_radius=ds.SHAPE_SM.radius.top_left,
            margin=ft.Margin(0, 0, 0, ds.space_sm),
        )

    def _cmd_card(self, c):
        status_colors = {"en_attente": ds.p.tertiary, "en_preparation": ds.p.primary,
                         "pret": ds.p.success, "livre": ds.p.text_soft, "annule": ds.p.error}
        sc = status_colors.get(c.get("statut", ""), ds.p.text_soft)
        return ft.Container(
            ft.Row([
                ft.Column([
                    ft.Text(f"#{str(c['id'])[:8]}", style=ds.textstyle("body_small"),
                            weight=ft.FontWeight.BOLD),
                    ft.Text(f"{float(c['total']):,.0f} FCFA", style=ds.textstyle("label_small")),
                ], spacing=0, expand=True),
                ft.Container(
                    ft.Text(c.get("statut", "—").replace("_", " "), size=11,
                            color=ds.p.on_primary),
                    padding=ft.Padding(ds.space_sm, 2, ds.space_sm, 2),
                    bgcolor=sc, border_radius=ds.SHAPE_FULL.radius.top_left,
                ),
            ]),
            padding=ds.space_md, bgcolor=ds.p.surface,
            border_radius=ds.SHAPE_SM.radius.top_left,
            margin=ft.Margin(0, 0, 0, ds.space_sm),
            border=ft.Border(left=ft.BorderSide(3, sc)),
        )

    # ═══════════ TAB 3 — CONTACT ═══════════

    def _contact_view(self):
        e = self._etab
        horaires = e.get("horaires")
        if isinstance(horaires, str):
            import json
            try: horaires = json.loads(horaires)
            except: horaires = None
        jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
        jours_fr = {"lundi": "Lundi", "mardi": "Mardi", "mercredi": "Mercredi",
                     "jeudi": "Jeudi", "vendredi": "Vendredi", "samedi": "Samedi",
                     "dimanche": "Dimanche"}

        return ft.Column([
            ft.Container(
                ft.Column([
                    ft.Text("Nous Contacter", style=ds.textstyle("headline_small")),
                    spacer(ds.space_md),
                    ft.Row([
                        ft.Icon(ft.Icons.LOCATION_ON, size=20, color=ds.p.primary),
                        spacer(ds.space_sm),
                        ft.Text(e.get("adresse", "—"), style=ds.textstyle("body_medium"),
                                expand=True),
                    ]),
                    spacer(ds.space_sm),
                    ft.Row([
                        ft.Icon(ft.Icons.PHONE, size=20, color=ds.p.primary),
                        spacer(ds.space_sm),
                        ft.Text(e.get("telephone", "—"), style=ds.textstyle("body_medium"),
                                expand=True),
                    ]),
                    spacer(ds.space_sm),
                    ft.Row([
                        ft.Icon(ft.Icons.EMAIL, size=20, color=ds.p.primary),
                        spacer(ds.space_sm),
                        ft.Text(e.get("email", "—"), style=ds.textstyle("body_medium"),
                                expand=True),
                    ]),
                    spacer(ds.space_sm) if e.get("site_web") else ft.Container(),
                    ft.Row([
                        ft.Icon(ft.Icons.LANGUAGE, size=20, color=ds.p.primary),
                        spacer(ds.space_sm),
                        ft.Text(e.get("site_web", ""), style=ds.textstyle("body_medium"),
                                expand=True),
                    ]) if e.get("site_web") else ft.Container(),
                ]),
                padding=ds.space_lg,
            ),
            # Horaires
            ft.Container(
                ft.Column([
                    ft.Text("Horaires d'ouverture", style=ds.textstyle("title_medium")),
                    spacer(ds.space_sm),
                    *[
                        ft.Row([
                            ft.Text(jours_fr.get(j, j), style=ds.textstyle("body_medium"),
                                    weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(horaires.get(j, "Fermé") if horaires else "—",
                                    style=ds.textstyle("body_medium"),
                                    color=ds.p.text_soft),
                        ])
                        for j in jours
                    ],
                ]),
                padding=ds.space_lg,
                bgcolor=ds.p.surface_variant,
            ),
            # Paiements acceptés
            ft.Container(
                ft.Column([
                    ft.Text("Moyens de paiement", style=ds.textstyle("title_medium")),
                    spacer(ds.space_sm),
                    ft.Text(e.get("moyens_paiement_acceptes", "Carte, Espèces"),
                            style=ds.textstyle("body_medium"), color=ds.p.text_soft),
                ]),
                padding=ds.space_lg,
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True)


def main(page: ft.Page):
    set_debug(True)
    page.title = "ArtizBoard — Portail Client"
    page.padding = 0
    page.window.width = 480
    page.window.height = 900
    ClientApp(page).run()

if __name__ == "__main__":
    ft.app(target=main)
