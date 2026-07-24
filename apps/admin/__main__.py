"""ArtizBoard — Application Admin (Livrable D)

Entry point : python -m admin_app

Écrans :
1. Premier démarrage → création admin + établissement
2. Login → email/mot de passe + QR code activation
3. Dashboard → menu latéral M3 + contenu
"""

import flet as ft
import psycopg2
import psycopg2.extras
import uuid
import base64, io, traceback
from datetime import datetime, timedelta
from pathlib import Path
import subprocess, hashlib, gzip, os, tempfile, shutil

from ArtizBoardCommon import ds
from ArtizBoardCommon.debug import safe_handler, set_debug
from ArtizBoardCommon.config_loader import get_db_config, get_supabase_config, get_backup_config
from ArtizBoardCommon.capture import capture_and_upload, FORMATS, CaptureError
from ArtizBoardCommon.components import (
    button, textfield, spacer, divider, headline, title, body, label,
    card, kpi_card, banner, section_header,
    ButtonVariant, CardVariant, Severity,
)

from apps.common.auth import AuthManager, AuthError
from apps.common.login import HeroPanel, PHOTO_URL
import dashboard_manager

# ═══════════════════════════════════════════════════════
#  Connexion DB + Supabase Storage
# ═══════════════════════════════════════════════════════

_db_host, _db_port, _db_name, _db_user, _db_pass = get_db_config()
_supabase_url, _supabase_anon, _supabase_service = get_supabase_config()

def upload_to_storage(file_bytes: bytes, filename: str, format_key: str = "carte_produit") -> str:
    """Upload via le pipeline Capture & Canvas. Retourne l'URL publique."""
    url, name = capture_and_upload(file_bytes, format_key, _supabase_url, _supabase_service)
    return url

def _get_conn():
    return psycopg2.connect(
        host=_db_host, port=_db_port, dbname=_db_name,
        user=_db_user, password=_db_pass,
        client_encoding="UTF8",
    )

# ═══════════════════════════════════════════════════════
#  App principale
# ═══════════════════════════════════════════════════════

class AdminApp:
    """Main admin application with routing."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.conn = _get_conn()
        self.auth = AuthManager(self.conn)
        self.user = None
        # FilePicker pour upload d'images (cree dans run() apres ds.apply)

    def _on_file_picked(self, e):
        if not e.files or e.files[0].path is None:
            return
        f = e.files[0]
        try:
            with open(f.path, "rb") as fh:
                data = fh.read()
            fmt = getattr(self, "_upload_format", "carte_produit")
            url = upload_to_storage(data, f.name, fmt)
            if self._pending_upload:
                self._pending_upload(url)
        except Exception as ex:
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Erreur upload: {ex}"), open=True)
            self.page.update()

    def run(self):
        set_debug(True)
        try:
            ds.apply(self.page)
            self.page.bgcolor = ds.p.background
            self.page.padding = 0

            if not self.auth.has_admin():
                self._show_first_boot()
            else:
                self._show_login()

            self.page.update()
        except Exception as e:
            self.page.controls.clear()
            self.page.add(
                ft.Column([
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ds.p.error),
                    spacer(ds.space_md),
                    headline("Erreur de connexion", size="medium"),
                    spacer(ds.space_sm),
                    body(f"Impossible de se connecter a la base de donnees.\n\n{type(e).__name__}: {e}",
                         color=ds.p.text_soft),
                    spacer(ds.space_lg),
                    button("Reessayer", icon=ft.Icons.REFRESH,
                           variant=ButtonVariant.FILLED,
                           on_click=safe_handler(lambda _: self.run(), "Admin.error.retry")),
                ], alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            )
            self.page.update()

    # ── Routing ──

    def _show_first_boot(self):
        # Fenêtre fixe comme le login
        self.page.window.resizable = False
        self.page.window.maximizable = False

        self.page.controls.clear()
        self.page.add(FirstBootScreen(self._on_first_boot_done))

    def _show_login(self, error: str = ""):
        # Mode login : fenêtre fixe, proportions φ pures
        self.page.window.resizable = False
        self.page.window.maximizable = False
        self.page.window.width = int(ds.golden_width(680))
        self.page.window.height = 680

        self.page.controls.clear()
        w_hero, w_form = ds.golden_split(self.page.window.width)
        login = LoginScreen(self._on_login, error)
        login.controls[0].width = w_hero
        login.controls[2].width = w_form
        self.page.add(login)

    def _show_dashboard(self):
        # Mode dashboard : plein écran disponible
        self.page.window.resizable = True
        self.page.window.maximizable = True
        self.page.window.maximized = True

        self.page.controls.clear()
        self.page.add(DashboardScreen(
            user=self.user,
            auth=self.auth,
            conn=self.conn,
            on_logout=self._on_logout,
        ))

    # ── Handlers ──

    def _on_first_boot_done(self, email: str, password: str, nom: str,
                            etablissement_nom: str, etablissement_type: str):
        try:
            uid, info = self.auth.create_first_admin(
                email, password, nom, etablissement_nom, etablissement_type
            )
            self.user = info
            self._show_dashboard()
        except Exception as e:
            self.page.controls.clear()
            self.page.add(FirstBootScreen(self._on_first_boot_done, error=str(e)))
            self.page.update()

    def _on_login(self, email: str, password: str):
        try:
            token, refresh, info = self.auth.login(email, password)
            self.user = info
            self.user["token"] = token
            self.user["refresh_token"] = refresh
            self._show_dashboard()
        except AuthError as e:
            self._show_login(error=str(e))

    def _on_logout(self):
        self.user = None
        self._show_login()


# ═══════════════════════════════════════════════════════
#  Écran Premier Démarrage
# ═══════════════════════════════════════════════════════

class FirstBootScreen(ft.Container):
    """Écran de création du premier admin + établissement."""

    def __init__(self, on_done: callable, error: str = ""):
        super().__init__(expand=True, alignment=ft.alignment.Alignment(0, 0),
                         bgcolor=ds.p.background, padding=0)

        self.on_done = on_done

        w_field = 400
        self.email = textfield(label="Email admin", prefix_icon="email",
                               hint="admin@monrestaurant.com", width=w_field)
        self.password = textfield(label="Mot de passe", password=True,
                                   prefix_icon="lock", width=w_field)
        self.nom = textfield(label="Votre nom", prefix_icon="person",
                             hint="Patrice", width=w_field)
        self.etablissement = textfield(label="Nom de l'établissement",
                                        prefix_icon="storefront",
                                        hint="Restaurant Le Gourmet", width=w_field)
        self.type_etab = ft.Dropdown(
            label="Type d'établissement",
            options=[
                ft.dropdown.Option("restaurant", "Restaurant"),
                ft.dropdown.Option("boutique_reelle", "Boutique Réelle"),
                ft.dropdown.Option("boutique_virtuelle", "Boutique Virtuelle"),
            ],
            value="restaurant",
            width=w_field,
            border_radius=ds.SHAPE_XS.radius.top_left,
        )
        self.error = ft.Text(error, color=ds.p.error, size=ds.typo.label_small.size)

        self.content = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.STOREFRONT, size=ds.icon_lg,
                                color=ds.p.primary),
                        spacer(ds.space_sm),
                        headline("Bienvenue sur ArtizBoard", size="medium"),
                    ]),
                    spacer(ds.space_xxs),
                    body("Premier démarrage — créez votre compte administrateur",
                         color=ds.p.text_soft),
                    spacer(ds.space_lg),
                    self.nom,
                    spacer(ds.space_sm),
                    self.email,
                    spacer(ds.space_sm),
                    self.password,
                    spacer(ds.space_sm),
                    self.etablissement,
                    spacer(ds.space_sm),
                    self.type_etab,
                    spacer(ds.space_sm),
                    self.error,
                    spacer(ds.space_lg),
                    button("Créer mon établissement", icon=ft.Icons.ROCKET_LAUNCH,
                           variant=ButtonVariant.FILLED, expand=True, height=52,
on_click=safe_handler(self._submit, "Admin.firstboot.submit")),
                ], horizontal_alignment=ft.CrossAxisAlignment.START),
                width=460,
            ),
            ft.Container(expand=True),
        ], alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _submit(self, e):
        email = self.email.value.strip()
        password = self.password.value
        nom = self.nom.value.strip()
        etab = self.etablissement.value.strip()
        type_etab = self.type_etab.value

        errors = []
        if not email: errors.append("Email requis")
        if not password or len(password) < 6: errors.append("Mot de passe (6+ car.)")
        if not nom: errors.append("Nom requis")
        if not etab: errors.append("Nom établissement requis")

        if errors:
            self.error.value = "  ".join(errors)
            self.error.update()
            return

        self.on_done(email, password, nom, etab, type_etab)


# ═══════════════════════════════════════════════════════
#  Écran Login Admin (paysage)
# ═══════════════════════════════════════════════════════

class LoginScreen(ft.Row):
    """Login paysage : HeroPanel à gauche + formulaire à droite."""

    def __init__(self, on_login: callable, error: str = ""):
        super().__init__(expand=True, spacing=0)

        self.error_msg = ft.Text(error, color=ds.p.error,
                                 size=ds.typo.label_small.size)

        w_field = 320
        self.email = textfield(label="Email", prefix_icon="email", width=w_field,
                               on_submit=safe_handler(self._submit, "Admin.login.submit"))
        self.password = textfield(label="Mot de passe", password=True,
                                   prefix_icon="lock", width=w_field,
                                   on_submit=safe_handler(self._submit, "Admin.login.submit"))

        hero = HeroPanel(photo_path=PHOTO_URL)
        form = ft.Container(
            ft.Column([
                ft.Container(expand=True),
                ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.STOREFRONT, size=ds.icon_md,
                                    color=ds.p.primary),
                            spacer(ds.space_xs),
                            headline("ArtizBoard Admin", size="medium"),
                        ]),
                        spacer(ds.space_xxs),
                        body("Connectez-vous a l'administration",
                             color=ds.p.text_soft),
                        spacer(ds.space_lg),
                        self.email,
                        spacer(ds.space_sm),
                        self.password,
                        spacer(ds.space_sm),
                        self.error_msg,
                        spacer(ds.space_lg),
                        button("Se connecter", variant=ButtonVariant.FILLED,
                               icon=ft.Icons.LOGIN, expand=True,
                               on_click=safe_handler(self._submit, "Admin.login.submit")),
                        spacer(ds.space_lg),
                        body("Ou utilisez un code d'activation",
                             size="small", color=ds.p.text_soft),
                        spacer(ds.space_sm),
                        ft.Row([
                            ft.Container(
                                ft.Icon(ft.Icons.QR_CODE_2, size=ds.icon_md,
                                        color=ds.p.primary),
                                padding=ds.space_md,
                                bgcolor=ds.p.primary_container,
                                border_radius=ds.SHAPE_SM.radius.top_left,
                            ),
                            spacer(ds.space_sm),
                            ft.Text("Scannez le QR code\npour vous connecter",
                                    style=ds.textstyle("body_small"),
                                    color=ds.p.text_soft),
                        ]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.START),
                    padding=ft.Padding(ds.space_lg, ds.space_lg,
                                       ds.space_lg, ds.space_lg),
                ),
                ft.Container(expand=True),
                ft.Text("v0.1.0  •  Admin  •  MIT", style=ds.textstyle("label_small"),
                        color=ds.p.text_disabled),
            ], alignment=ft.MainAxisAlignment.CENTER,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            bgcolor=ds.p.background,
            alignment=ft.alignment.Alignment(0, 0),
        )

        self.controls = [
            hero,
            ft.VerticalDivider(width=ds.border_width, color=ds.p.outline_variant),
            form,
        ]
        self.on_login_cb = on_login

    def _submit(self, e):
        email = self.email.value.strip()
        password = self.password.value
        if not email:
            self.error_msg.value = "Email requis"
            self.error_msg.update()
            return
        if not password:
            self.error_msg.value = "Mot de passe requis"
            self.error_msg.update()
            return
        self.error_msg.value = ""
        self.error_msg.update()
        self.on_login_cb(email, password)


# ═══════════════════════════════════════════════════════
#  Dashboard — menu latéral + contenu
# ═══════════════════════════════════════════════════════

class DashboardScreen(ft.Row):
    """Dashboard admin avec sidebar M3."""

    def __init__(self, user: dict, auth: AuthManager, conn,
                 on_logout: callable):
        super().__init__(expand=True, spacing=0)
        self.user = user
        self.auth = auth
        self.conn = conn
        self.on_logout = on_logout
        self._selected = "dashboard"
        self._pending_upload = None
        # Détection du type d'établissement
        cur = conn.cursor()
        cur.execute("SELECT type FROM etablissements WHERE id=%s", (user["etablissement_id"],))
        row = cur.fetchone()
        self._est_type = row[0] if row else "restaurant"
        cur.close()
        self.content_area = ft.Container(expand=True, padding=ds.space_lg)
        self._rebuild()

    def _on_file_picked(self, e):
        if not e.files or e.files[0].path is None:
            return
        f = e.files[0]
        try:
            with open(f.path, "rb") as fh:
                data = fh.read()
            fmt = getattr(self, "_upload_format", "carte_produit")
            url = upload_to_storage(data, f.name, fmt)
            if self._pending_upload:
                self._pending_upload(url)
        except Exception as ex:
            traceback.print_exc()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Erreur upload: {ex}"), open=True)
                self.page.update()

    def _rebuild(self):
        """Reconstruit le Row complet (sidebar + content)."""
        self.controls.clear()
        self.controls.append(self._sidebar())
        self.controls.append(self.content_area)
        self.content_area.content = self._build_content(self._selected)

    def _sidebar(self):
        logo_src = "http://127.0.0.1:8080/uploads/logo/logo.png"
        items = [spacer(ds.space_md),
                 ft.Container(ft.Image(src=logo_src, fit="contain", height=50,
                                       error_content=ft.Icon(ft.Icons.STOREFRONT,size=ds.icon_lg,color=ds.p.primary)),
                             padding=ds.space_sm, alignment=ft.alignment.Alignment(-1,0)),
                 headline(self.user.get('etablissement_nom', 'ArtizBoard'), size="medium"),
                 spacer(ds.space_xxs),
                 label(f"Admin  •  {self.user.get('nom', '')}", color=ds.p.text_soft),
                 spacer(ds.space_lg)]

        for k, lbl, ico in [
            ("dashboard", "Dashboard", ft.Icons.DASHBOARD),
            ("catalogue", "Catalogue", ft.Icons.INVENTORY),
            ("commandes", "Commandes", ft.Icons.RECEIPT),
            ("users", "Utilisateurs", ft.Icons.GROUPS),
            ("etablissement", "Établissement", ft.Icons.STOREFRONT),
            ("rapports", "Rapports", ft.Icons.BAR_CHART),
            ("sauvegardes", "Sauvegardes", ft.Icons.BACKUP),
        ]:
            sel = self._selected == k
            items.append(ft.Container(
                ft.Row([
                    ft.Icon(ico, size=ds.icon_sm, color=ds.p.primary if sel else ds.p.text_soft),
                    spacer(ds.space_sm),
                    ft.Text(lbl, style=ds.textstyle("body_medium"),
                            color=ds.p.text_strong if sel else ds.p.text_soft,
                            weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL),
                ]),
                padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
                bgcolor=ds.p.primary_container if sel else None,
                border_radius=ds.SHAPE_SM.radius.top_left,
                on_click=safe_handler(lambda e, kk=k: self._navigate(kk), "Admin.sidebar.navigate"),
            ))

        items.append(ft.Container(expand=True))
        items.append(divider())
        items.append(spacer(ds.space_sm))
        items.append(ft.Container(
            ft.Column([
                ft.Text("© 2026 ArtizBoard · MIT", size=10, color=ds.p.text_disabled),
                ft.Text("Licence libre et permissive", size=9, color=ds.p.text_disabled),
            ], spacing=2),
            padding=ft.Padding(ds.space_md, 0, ds.space_md, ds.space_sm),
        ))
        items.append(ft.Container(
            ft.Row([
                ft.Icon(ft.Icons.LOGOUT, size=ds.icon_sm, color=ds.p.text_soft),
                spacer(ds.space_sm),
                ft.Text("Deconnexion", style=ds.textstyle("body_medium"), color=ds.p.text_soft),
            ]),
            padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
            border_radius=ds.SHAPE_SM.radius.top_left,
            on_click=safe_handler(lambda e: self.on_logout(), "Admin.sidebar.logout"),
        ))

        return ft.Container(
            ft.Column(items, spacing=0), width=260, bgcolor=ds.p.surface,
            border=ft.Border(right=ft.BorderSide(1, ds.p.outline_variant)),
            padding=ft.Padding(ds.space_md, 0, ds.space_md, ds.space_md),
        )

    def _navigate(self, key: str):
        if key == "logout":
            self.on_logout()
            return
        self._selected = key
        self._rebuild()
        self.update()

    def _build_content(self, key: str):
        if key == "dashboard":
            return self._dashboard_content()
        elif key == "catalogue":
            return self._catalogue_content()
        elif key == "commandes":
            return self._commandes_content()
        elif key == "users":
            return self._users_content()
        elif key == "etablissement":
            return self._etablissement_content()
        elif key == "rapports":
            return self._rapports_content()
        elif key == "sauvegardes":
            return self._backups_content()
        return self._dashboard_content()

    def _dashboard_content(self) -> ft.Column:
        now = datetime.now()
        if not hasattr(self, '_dd'): self._dd = 30
        debut = (now-timedelta(days=self._dd)).strftime("%Y-%m-%d"); fin = now.strftime("%Y-%m-%d")
        def sd(d): self._dd = d; self._navigate("dashboard")

        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id,nom FROM utilisateurs WHERE etablissement_id=%s AND deleted_at IS NULL ORDER BY nom",(self.user["etablissement_id"],)); sl=[dict(r) for r in cur.fetchall()]
        cur.execute("SELECT id,nom FROM categories WHERE etablissement_id=%s AND deleted_at IS NULL ORDER BY nom",(self.user["etablissement_id"],)); cl=[dict(r) for r in cur.fetchall()]
        cur.close()
        ana_s = ft.Dropdown(options=[ft.dropdown.Option("","Tous serveurs")]+[ft.dropdown.Option(str(s["id"]),s["nom"][:15]) for s in sl],value="",width=150)
        ana_c = ft.Dropdown(options=[ft.dropdown.Option("","Toutes cat.")]+[ft.dropdown.Option(str(c["id"]),c["nom"][:15]) for c in cl],value="",width=150)

        total_kpi = ft.Row(spacing=ds.space_md)
        ch1 = ft.Column(spacing=0, expand=True)
        ch2 = ft.Column(spacing=0, expand=True)
        ch3 = ft.Column(spacing=0, expand=True)
        alerts = ft.Column(spacing=ds.space_xxs)

        def make_chart(title, rows, key="ca", label_key="j", color=ds.p.primary, height=140):
            """Clean bar chart: fixed-width bars, baseline, compact labels."""
            c = ft.Column(spacing=0, expand=True)
            mx = max(float(rr[key]) for rr in rows) if rows else 1
            c.controls.append(ft.Text(title, size=13, weight=ft.FontWeight.BOLD))
            c.controls.append(ft.Text(f"Max: {mx:,.0f} FCFA", size=9, color=ds.p.text_soft))
            # Chart area with fixed height, bars bottom-aligned
            chart = ft.Container(
                ft.Row([ft.Container(
                    ft.Column([
                        ft.Text(f"{float(rr[key])/1000:.0f}k", size=7, color=ds.p.text_soft, text_align=ft.TextAlign.CENTER),
                        ft.Container(expand=True),
                        ft.Container(width=22, height=max(4,int(float(rr[key])/mx*(height-40))), bgcolor=color,
                                    border_radius=ft.BorderRadius(top_left=3,top_right=3,bottom_left=0,bottom_right=0)),
                        ft.Text(str(rr[label_key])[:8], size=7, color=ds.p.primary, text_align=ft.TextAlign.CENTER),
                    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ) for rr in rows], spacing=4, vertical_alignment=ft.CrossAxisAlignment.END),
                height=height, border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)),
            )
            c.controls.append(chart)
            return c

        def refresh(e=None):
            days=self._dd; d=(now-timedelta(days=days)).strftime("%Y-%m-%d"); f=now.strftime("%Y-%m-%d")
            params=[self.user["etablissement_id"],d,f]; where="WHERE c.etablissement_id=%s AND c.statut_paiement='paye' AND c.created_at>=%s AND c.created_at<%s::date+1 AND c.deleted_at IS NULL"
            if ana_s.value: where+=" AND c.staff_id=%s"; params.append(ana_s.value)
            if ana_c.value: where+=" AND c.id IN (SELECT DISTINCT lc.commande_id FROM lignes_commande lc JOIN produits p ON lc.produit_id=p.id WHERE p.categorie_id=%s AND lc.deleted_at IS NULL)"; params.append(ana_c.value)

            cur2=self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # KPI totals
            cur2.execute(f"SELECT COALESCE(SUM(DISTINCT c.total),0)::numeric as ca,COUNT(DISTINCT c.id)::int as nb FROM commandes c {where}",tuple(params)); r=cur2.fetchone()
            ca2=float(r["ca"]); nb2=int(r["nb"]); pm2=ca2/nb2 if nb2>0 else 0
            total_kpi.controls.clear()
            for v,l in [(f"{ca2:,.0f}F",f"CA {days}j"),(str(nb2),"Cmd"),(f"{pm2:,.0f}F","Panier")]:
                total_kpi.controls.append(ft.Container(ft.Column([ft.Text(v,size=18,weight=ft.FontWeight.BOLD,color=ds.p.primary),ft.Text(l,size=10,color=ds.p.text_soft)],spacing=0),padding=ds.space_sm,bgcolor=ds.p.primary_container,border_radius=ds.SHAPE_MD.radius.top_left,expand=True))

            # Chart 1: CA/jour
            cur2.execute(f"SELECT DATE(c.created_at) as j,COALESCE(SUM(DISTINCT c.total),0)::numeric as ca FROM commandes c {where} GROUP BY DATE(c.created_at) ORDER BY j LIMIT 30",tuple(params))
            r1=cur2.fetchall()
            ch1_ctrl = make_chart("CA par jour", r1, "ca", "j")
            ch1.controls.clear(); ch1.controls.append(ch1_ctrl)

            # Chart 2: CA/serveur
            cur2.execute(f"SELECT u.nom,COALESCE(SUM(DISTINCT c.total),0)::numeric as ca FROM commandes c JOIN utilisateurs u ON c.staff_id=u.id {where} AND u.deleted_at IS NULL GROUP BY u.nom ORDER BY ca DESC LIMIT 10",tuple(params))
            r2=cur2.fetchall()
            ch2_ctrl = make_chart("CA par serveur", r2, "ca", "nom", ds.p.tertiary)
            ch2.controls.clear(); ch2.controls.append(ch2_ctrl)

            # Chart 3: CA/categorie
            cur2.execute(f"SELECT cat.nom,COALESCE(SUM(DISTINCT lc.quantite*lc.prix_unitaire),0)::numeric as ca FROM commandes c JOIN lignes_commande lc ON c.id=lc.commande_id JOIN produits p ON lc.produit_id=p.id JOIN categories cat ON p.categorie_id=cat.id {where} AND lc.deleted_at IS NULL GROUP BY cat.nom ORDER BY ca DESC LIMIT 10",tuple(params))
            r3=cur2.fetchall()
            ch3_ctrl = make_chart("CA par categorie", r3, "ca", "nom", ds.p.success)
            ch3.controls.clear(); ch3.controls.append(ch3_ctrl)

            # Alerts
            cur2.execute("SELECT nom,stock,stock_alerte FROM produits WHERE etablissement_id=%s AND deleted_at IS NULL AND stock<=stock_alerte ORDER BY stock LIMIT 5",(self.user["etablissement_id"],)); al=cur2.fetchall()
            alerts.controls.clear()
            if al: alerts.controls.append(ft.Text("Alertes",size=11,weight=ft.FontWeight.BOLD,color=ds.p.error))
            for a in al: alerts.controls.append(ft.Text(f"{a['nom'][:25]}: {a['stock']}/{a['stock_alerte']}",size=10,color=ds.p.error))

            cur2.close()
            try: ch1.update();ch2.update();ch3.update();alerts.update();total_kpi.update()
            except RuntimeError: pass

        ana_s.on_change = refresh
        ana_c.on_change = refresh

        filters = ft.Row(spacing=ds.space_xs, wrap=True)
        for dd,lbl in [(1,"1j"),(7,"7j"),(30,"30j"),(90,"90j"),(365,"1an")]:
            sel=self._dd==dd
            filters.controls.append(ft.Container(ft.Text(lbl,size=11,weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL,color=ds.p.on_primary if sel else ds.p.primary),padding=ft.Padding(ds.space_sm,ds.space_xs,ds.space_sm,ds.space_xs),bgcolor=ds.p.primary if sel else None,border=ft.Border.all(1,ds.p.primary) if not sel else None,border_radius=ds.SHAPE_FULL.radius.top_left,on_click=lambda e,d=dd:sd(d)))
        filters.controls.extend([ft.Container(width=10),ft.Text("|",size=14,color=ds.p.outline_variant),ana_s,ft.Text("|",size=14,color=ds.p.outline_variant),ana_c,
            ft.Container(width=10),ft.FilledTonalButton(content=ft.Text("Refresh"),icon=ft.Icons.REFRESH,on_click=refresh,height=30)])

        refresh()
        return ft.Column([ft.Text("Tableau de bord",size=22,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),ft.Text(f"{debut} -> {fin}",size=11,color=ds.p.text_soft),spacer(ds.space_sm),filters,spacer(ds.space_md),total_kpi,spacer(ds.space_md),ch1,spacer(ds.space_md),ch2,spacer(ds.space_md),ch3,spacer(ds.space_md),alerts],expand=True,scroll=ft.ScrollMode.AUTO)

    def _placeholder(self, title: str) -> ft.Column:
        return ft.Column([
            section_header(title),
            spacer(ds.space_lg),
            card(
                title=f"{title} — En développement",
                content=body("Cette section sera disponible prochainement.",
                             color=ds.p.text_soft),
                variant=CardVariant.OUTLINED,
            ),
        ])

    # ══════════════════════════════════════════════════
    #  Catalogue produits
    # ══════════════════════════════════════════════════

    def _fetch_produits(self, search: str = "", categorie_id: str = ""):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT p.*, c.nom AS categorie_nom
            FROM produits p
            JOIN categories c ON p.categorie_id = c.id
            WHERE p.etablissement_id = %s
              AND p.deleted_at IS NULL
              AND c.deleted_at IS NULL
        """
        params = [self.user["etablissement_id"]]
        if search:
            query += " AND (p.nom ILIKE %s OR p.description ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        if categorie_id:
            query += " AND p.categorie_id = %s"
            params.append(categorie_id)
        query += " ORDER BY p.nom"
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _fetch_categories(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM categories WHERE etablissement_id = %s AND deleted_at IS NULL ORDER BY nom",
            (self.user["etablissement_id"],),
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _save_produit(self, data: dict):
        cur = self.conn.cursor()
        eid = self.user["etablissement_id"]
        uid = self.user["id"]

        if data.get("id"):
            cur.execute("""
                UPDATE produits SET nom=%s, description=%s, categorie_id=%s,
                prix=%s, taux_tva=%s, stock=%s, stock_alerte=%s,
                permets_commande=%s, photo_url=%s, updated_by=%s, updated_at=NOW(),
                version = version + 1
                WHERE id=%s AND version=%s AND deleted_at IS NULL
            """, (
                data["nom"], data.get("description", ""), data["categorie_id"],
                data["prix"], data.get("taux_tva", 0), data.get("stock", 0),
                data.get("stock_alerte", 5), data.get("permets_commande", True),
                data.get("photo_url", ""),
                uid, data["id"], data.get("version", 1),
            ))
            if cur.rowcount == 0:
                self.conn.rollback()
                cur.close()
                raise ValueError("Produit modifié par un autre utilisateur. Rechargez.")
        else:
            pid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO produits (id, categorie_id, nom, description, photo_url, prix,
                taux_tva, stock, stock_alerte, permets_commande,
                etablissement_id, created_by, updated_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                pid, data["categorie_id"], data["nom"],
                data.get("description", ""), data.get("photo_url", ""), data["prix"],
                data.get("taux_tva", 0), data.get("stock", 0),
                data.get("stock_alerte", 5), data.get("permets_commande", True),
                eid, uid, uid,
            ))
        self.conn.commit()
        cur.close()

    def _delete_produit(self, produit_id: str):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE produits SET deleted_at=NOW(), updated_by=%s WHERE id=%s AND deleted_at IS NULL",
            (self.user["id"], produit_id),
        )
        self.conn.commit()
        cur.close()

    # ══════════════════════════════════════════════════
    #  Catalogue 3 panneaux
    # ══════════════════════════════════════════════════

    def _save_categorie(self, data: dict):
        cur = self.conn.cursor()
        cid = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO categories (id, nom, icone, etablissement_id, created_by, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cid, data["nom"], data.get("icone", "category"),
              self.user["etablissement_id"], self.user["id"], self.user["id"]))
        self.conn.commit()
        cur.close()
        return cid

    def _delete_cat_direct(self, cat: dict):
        """Suppression directe sans dialogue."""
        try:
            self._delete_categorie(str(cat["id"]))
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Categorie '{cat['nom']}' supprimee"), open=True)
            self.page.update()
            self._catsel = None; self._prodsel = None
            self._navigate("catalogue")
        except ValueError as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(str(ex)), open=True)
            self.page.update()

    def _delete_categorie(self, cat_id: str):
        """Soft delete une categorie. Empeche si elle a des produits."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM produits WHERE categorie_id=%s AND deleted_at IS NULL", (cat_id,))
        if cur.fetchone()[0] > 0:
            cur.close()
            raise ValueError("Cette categorie contient des produits. Supprimez-les d'abord.")
        cur.execute(
            "UPDATE categories SET deleted_at=NOW(), updated_by=%s WHERE id=%s AND deleted_at IS NULL",
            (self.user["id"], cat_id))
        self.conn.commit()
        cur.close()

    def _confirm_delete_cat(self, cat: dict):
        def do_delete(e):
            try:
                self._delete_categorie(str(cat["id"]))
                dlg.open = False; self.page.update()
                self._navigate("catalogue")
            except ValueError as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(str(ex)), open=True)
                self.page.update()
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmer"),
            content=ft.Text(f"Supprimer la categorie '{cat['nom']}' ?"),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: setattr(dlg,'open',False) or self.page.update()),
                ft.FilledButton(content=ft.Text("Supprimer"), icon=ft.Icons.DELETE, on_click=do_delete),
            ],
        )
        self.page.show_dialog(dlg)



    def _catalogue_content(self):
        self._catsel = None   # selected category id
        self._prodsel = None  # selected product id
        categories = self._fetch_categories()

        # ── Panneau 1 : Catégories ──
        cat_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

        # Initialisation directe (pas de .update() — pas encore monté)
        for c in categories:
            cid = str(c["id"])
            is_sel = cid == self._catsel
            cat_list.controls.append(
                        ft.Container(
                            ft.Row([
                                ft.Icon(ft.Icons.CIRCLE if is_sel else ft.Icons.CIRCLE_OUTLINED,
                                        size=10, color=ds.p.primary if is_sel else ds.p.text_disabled),
                                spacer(ds.space_xs),
                                ft.Container(
                                    ft.Text(c["nom"], style=ds.textstyle("body_medium"),
                                            color=ds.p.primary if is_sel else ds.p.text_strong,
                                            weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL),
                                    expand=True,
                                    on_click=safe_handler(lambda e, cc=c: _select_cat(cc), "Admin.catalogue.select_cat"),
                                ),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_size=14, icon_color=ds.p.error,
                                             tooltip="Supprimer",
                                             on_click=safe_handler(lambda e, cc=c: self._delete_cat_direct(cc), "Admin.catalogue.delete_cat")),
                            ]),
                    padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
                    bgcolor=ds.p.primary_container if is_sel else None,
                    border_radius=ds.SHAPE_XS.radius.top_left,
                )
            )

        def refresh_cats():
            cats = self._fetch_categories()
            cat_list.controls.clear()
            for c in cats:
                cid = str(c["id"])
                is_sel = cid == self._catsel
                cat_list.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.CIRCLE if is_sel else ft.Icons.CIRCLE_OUTLINED,
                                    size=10, color=ds.p.primary if is_sel else ds.p.text_disabled),
                            spacer(ds.space_xs),
                            ft.Container(
                                ft.Text(c["nom"], style=ds.textstyle("body_medium"),
                                        color=ds.p.primary if is_sel else ds.p.text_strong,
                                        weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL),
                                expand=True,
                                on_click=safe_handler(lambda e, cc=c: _select_cat(cc), "Admin.catalogue.select_cat"),
                            ),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_size=14, icon_color=ds.p.error,
                                         tooltip="Supprimer",
                                         on_click=safe_handler(lambda e, cc=c: self._delete_cat_direct(cc), "Admin.catalogue.delete_cat")),
                        ]),
                        padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
                        bgcolor=ds.p.primary_container if is_sel else None,
                        border_radius=ds.SHAPE_XS.radius.top_left,
                    )
                )
            try:
                cat_list.update()
            except RuntimeError:
                pass

        # ── Panneau 2 : Produits ──
        prod_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
        prod_header = headline("Produits", size="small")

        def refresh_prods():
            prods = self._fetch_produits(categorie_id=self._catsel) if self._catsel else []
            prod_list.controls.clear()
            if not prods:
                prod_list.controls.append(
                    ft.Text("Aucun produit dans cette categorie",
                            style=ds.textstyle("body_small"), color=ds.p.text_disabled,
                            italic=True)
                )
            for p in prods:
                pid = str(p["id"])
                is_sel = pid == self._prodsel
                sc = ds.p.error if p["stock"] <= p.get("stock_alerte", 5) else ds.p.text_soft
                prod_list.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Container(
                                ft.Text(str(p["stock"]), style=ds.textstyle("label_small"), color=sc),
                                alignment=ft.alignment.Alignment(0, 0),
                                width=28, height=28,
                                bgcolor=ds.p.surface_variant,
                                border_radius=ds.SHAPE_XS.radius.top_left,
                            ),
                            spacer(ds.space_sm),
                            ft.Column([
                                ft.Text(p["nom"], style=ds.textstyle("body_medium"),
                                        weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL),
                                ft.Text(f"{float(p['prix']):,.0f} FCFA", style=ds.textstyle("label_small"),
                                        color=ds.p.text_soft),
                            ], spacing=0, expand=True),
                        ]),
                        padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
                        bgcolor=ds.p.primary_container if is_sel else None,
                        border_radius=ds.SHAPE_XS.radius.top_left,
                        on_click=safe_handler(lambda e, pp=p: _select_prod(pp), "Admin.catalogue.select_prod"),
                    )
                )
            if prod_list.page: prod_list.update()

        # ── Panneau 3 : Détail produit ──
        detail_panel = ft.Container(
            ft.Column([
                ft.Icon(ft.Icons.INVENTORY_2, size=48, color=ds.p.text_disabled,
                        opacity=0.5),
                spacer(ds.space_sm),
                ft.Text("Selectionnez un produit", style=ds.textstyle("body_medium"),
                        color=ds.p.text_soft, italic=True),
            ], alignment=ft.MainAxisAlignment.CENTER,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, bgcolor=ds.p.surface_variant,
            border_radius=ds.SHAPE_MD.radius.top_left,
            padding=ds.space_lg,
        )

        def refresh_detail():
            nonlocal detail_panel
            if not self._prodsel:
                detail_panel.content = ft.Column([
                    ft.Icon(ft.Icons.INVENTORY_2, size=48, color=ds.p.text_disabled, opacity=0.5),
                    spacer(ds.space_sm),
                    ft.Text("Selectionnez un produit", style=ds.textstyle("body_medium"),
                            color=ds.p.text_soft, italic=True),
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                detail_panel.bgcolor = ds.p.surface_variant
            else:
                cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute("""
                    SELECT p.*, c.nom AS categorie_nom
                    FROM produits p JOIN categories c ON p.categorie_id = c.id
                    WHERE p.id = %s AND p.deleted_at IS NULL
                """, (self._prodsel,))
                p = cur.fetchone()
                cur.close()
                if not p:
                    return

                sc = ds.p.error if p["stock"] <= p.get("stock_alerte", 5) else ds.p.success
                detail_panel.bgcolor = ds.p.background
                _up = "http://127.0.0.1:8080/uploads/"
                detail_panel.content = ft.Column([
                    # Photo
                    ft.Container(
                        ft.Image(src=(_up + p["photo_url"]) if p["photo_url"] and not p["photo_url"].startswith("http") else (p.get("photo_url","") or ""),
                                 fit="cover",
                                 border_radius=ds.SHAPE_MD.radius.top_left),
                        height=200, border_radius=ds.SHAPE_MD.radius.top_left,
                        bgcolor=ds.p.surface_variant,
                    ) if p.get("photo_url") else ft.Container(
                        ft.Icon(ft.Icons.IMAGE, size=64, color=ds.p.text_disabled),
                        height=200, bgcolor=ds.p.surface_variant,
                        border_radius=ds.SHAPE_MD.radius.top_left,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    spacer(ds.space_sm),
                    headline(p["nom"], size="small"),
                    spacer(ds.space_xxs),
                    ft.Text(p.get("categorie_nom", ""), style=ds.textstyle("label_small"),
                            color=ds.p.text_soft),
                    spacer(ds.space_sm),
                    ft.Row([
                        ft.Container(
                            ft.Column([
                                ft.Text("PRIX", style=ds.textstyle("label_small"), color=ds.p.text_soft),
                                ft.Text(f"{float(p['prix']):,.0f} FCFA", style=ds.textstyle("title_medium"),
                                        color=ds.p.primary),
                            ]),
                        ),
                        spacer(ds.space_lg),
                        ft.Container(
                            ft.Column([
                                ft.Text("STOCK", style=ds.textstyle("label_small"), color=ds.p.text_soft),
                                ft.Text(str(p["stock"]), style=ds.textstyle("title_medium"), color=sc),
                            ]),
                        ),
                        spacer(ds.space_lg),
                        ft.Container(
                            ft.Column([
                                ft.Text("ALERTE", style=ds.textstyle("label_small"), color=ds.p.text_soft),
                                ft.Text(str(p.get("stock_alerte", 5)), style=ds.textstyle("body_medium")),
                            ]),
                        ),
                    ]),
                    spacer(ds.space_sm),
                    ft.Text("DESCRIPTION", style=ds.textstyle("label_small"), color=ds.p.text_soft),
                    ft.Markdown(p.get("description", "Aucune description") or "",
                                extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                                on_tap_link=lambda e: e.page.launch_url(e.data)),
                    spacer(ds.space_sm),
                    ft.Row([
                        ft.Text(f"TVA : {float(p.get('taux_tva', 0)):.0f}%",
                                style=ds.textstyle("label_small"), color=ds.p.text_soft),
                        ft.Text(f"Visible : {'Oui' if p['permets_commande'] else 'Non'}",
                                style=ds.textstyle("label_small"),
                                color=ds.p.success if p['permets_commande'] else ds.p.error),
                    ]),
                    spacer(ds.space_lg),
                    ft.Row([
                        button("Modifier", variant=ButtonVariant.TONAL,
                               icon=ft.Icons.EDIT,
                               on_click=lambda e: print("MODIFIER CLICKED", p["nom"]) or self._edit_produit(str(p["id"]))),
                        spacer(ds.space_sm),
                        button("Supprimer", variant=ButtonVariant.TEXT,
                               icon=ft.Icons.DELETE,
                               on_click=lambda e: print("SUPPRIMER CLICKED", p["nom"]) or self._confirm_delete(str(p["id"]))),
                    ]),
                ], scroll=ft.ScrollMode.AUTO, spacing=0)
            if detail_panel.page: detail_panel.update()

        # ── Handlers ──
        def _select_cat(cat):
            self._catsel = str(cat["id"])
            self._prodsel = None
            refresh_cats()
            refresh_prods()
            refresh_detail()

        def _select_prod(prod):
            self._prodsel = str(prod["id"])
            refresh_prods()
            refresh_detail()

        def add_cat_dialog(e):
            nom_f = ft.TextField(label="Nom de la categorie", width=300)
            err = ft.Text("", color=ds.p.error, size=11)
            def save_cat(e):
                if not nom_f.value.strip():
                    err.value = "Nom requis"; err.update(); return
                self._save_categorie({"nom": nom_f.value.strip(), "icone": "category"})
                dlg.open = False; self.page.update()
                self._catsel = None; self._prodsel = None
                refresh_cats(); refresh_prods(); refresh_detail()
            dlg = ft.AlertDialog(
                title=ft.Text("Nouvelle categorie"),
                content=ft.Column([nom_f, err], width=320),
                actions=[ft.TextButton("Annuler", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update()),
                         ft.FilledButton(content=ft.Text("Creer"), icon=ft.Icons.ADD, on_click=save_cat)],
            )
            self.page.show_dialog(dlg)

        # ── Build full layout ──
        # refresh_cats n'est pas appelée ici (population inline déjà faite)

        # Category panel
        left = ft.Container(
            ft.Column([
                section_header("Categories", action=ft.IconButton(
                    icon=ft.Icons.ADD, icon_size=18, tooltip="Ajouter",
                    on_click=add_cat_dialog,
                )),
                spacer(ds.space_sm),
                cat_list,
            ]),
            width=300,
            bgcolor=ds.p.background,
        )

        # Products panel
        mid = ft.Container(
            ft.Column([
                section_header("Produits"),
                prod_list,
                spacer(ds.space_sm),
                button("Ajouter un produit", variant=ButtonVariant.TEXT,
                       icon=ft.Icons.ADD,
                       on_click=safe_handler(lambda e: self._edit_produit(None, cat_id=self._catsel), "Admin.catalogue.add_produit")),
            ]),
            expand=1,
            bgcolor=ds.p.surface,
            border=ft.Border(left=ft.BorderSide(1, ds.p.outline_variant),
                             right=ft.BorderSide(1, ds.p.outline_variant)),
            padding=ft.Padding(ds.space_md, 0, ds.space_md, ds.space_md),
        )

        # Detail panel
        right = ft.Container(
            detail_panel,
            expand=2,
            bgcolor=ds.p.background,
            padding=ft.Padding(ds.space_lg, 0, ds.space_lg, ds.space_md),
        )

        return ft.Column([
            section_header("Catalogue"),
            spacer(ds.space_sm),
            ft.Row([left, mid, right], expand=True, spacing=0),
        ], expand=True)

    def _edit_produit(self, produit_id: str = None, cat_id: str = None):
        import time
        now = time.time()
        if hasattr(self, '_edit_produit_last') and now - self._edit_produit_last < 0.5:
            return
        self._edit_produit_last = now

        categories = self._fetch_categories()
        produit = None
        if produit_id:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM produits WHERE id=%s AND deleted_at IS NULL", (produit_id,))
            produit = cur.fetchone()
            cur.close()

        w = 360
        nom = ft.TextField(label="Nom", value=produit["nom"] if produit else "", width=w)
        cat = ft.Dropdown(
            label="Categorie",
            options=[ft.dropdown.Option(str(c["id"]), c["nom"]) for c in categories],
            value=str(produit["categorie_id"]) if produit else (cat_id or None),
            width=w,
        )
        prix = ft.TextField(label="Prix (FCFA)", value=str(produit["prix"]) if produit else "", width=w)
        photo_url = ft.TextField(label="Photo (nom du fichier)", value=produit.get("photo_url","") if produit else "", width=w,
                                hint_text="ex: riz_gras.jpg")
        photo_status = ft.Text("Placez le fichier dans /uploads/",
                               size=11, color=ds.p.text_soft)

        upload_btn = ft.FilledTonalButton(content=ft.Text("Parcourir..."),
                                          icon=ft.Icons.UPLOAD_FILE,
                                          on_click=upload_photo)
        desc = ft.TextField(label="Description (Markdown)", value=produit["description"] if produit else "",
                           width=w, multiline=True, min_lines=2, max_lines=4,
                           hint_text="**gras** *italique* - liste")
        stock = ft.TextField(label="Stock", value=str(produit["stock"]) if produit else "0", width=w)
        alerte = ft.TextField(label="Seuil alerte", value=str(produit.get("stock_alerte",5)) if produit else "5", width=w)
        tva = ft.TextField(label="TVA (%)", value=str(produit.get("taux_tva",0)) if produit else "0", width=w)
        disponible = ft.Checkbox(label="Disponible a la commande", value=produit["permets_commande"] if produit else True)
        err = ft.Text("", color=ds.p.error, size=11)

        def save(e):
            try:
                p = float(prix.value or 0)
                s = int(stock.value or 0)
            except ValueError:
                err.value = "Prix et stock doivent etre numeriques"; err.update(); return
            if not cat.value:
                err.value = "Categorie requise"; err.update(); return
            data = {
                "id": produit_id, "nom": nom.value.strip(), "categorie_id": cat.value,
                "description": desc.value.strip(), "prix": p, "taux_tva": float(tva.value or 0),
                "stock": s, "stock_alerte": int(alerte.value or 5), "permets_commande": disponible.value,
                "photo_url": photo_url.value.strip(),
            }
            if produit: data["version"] = produit["version"]
            try:
                self._save_produit(data)
                dlg.open = False; self.page.update()
                self._navigate("catalogue")
            except ValueError as e:
                err.value = str(e); err.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Modifier" if produit else "Ajouter un produit"),
            content=ft.Column([
                nom, cat, prix, photo_url, desc, stock, alerte, tva, disponible, err,
            ], height=400, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: setattr(dlg,'open',False) or self.page.update()),
                ft.FilledButton(content=ft.Text("Enregistrer"), icon=ft.Icons.SAVE, on_click=save),
            ],
        )
        self.page.show_dialog(dlg)

    def _confirm_delete(self, produit_id: str):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT nom FROM produits WHERE id=%s", (produit_id,))
        p = cur.fetchone(); cur.close()
        def do_delete(e):
            self._delete_produit(produit_id)
            dlg.open = False; self.page.update()
            self._navigate("catalogue")
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmer la suppression"),
            content=ft.Text(f"Supprimer '{p['nom']}' ?"),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: setattr(dlg,'open',False) or self.page.update()),
                ft.FilledButton(content=ft.Text("Supprimer"), icon=ft.Icons.DELETE, on_click=do_delete),
            ],
        )
        self.page.show_dialog(dlg)

    # ══════════════════════════════════════════════════
    #  Utilisateurs & Rôles
    # ══════════════════════════════════════════════════

    def _fetch_users(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT u.*, r.nom AS role_nom
            FROM utilisateurs u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.etablissement_id = %s AND u.deleted_at IS NULL
            ORDER BY u.created_at DESC
        """, (self.user["etablissement_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _fetch_roles(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM roles WHERE deleted_at IS NULL ORDER BY nom")
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def _save_user(self, data: dict):
        cur = self.conn.cursor()
        from apps.common.auth import AuthManager
        auth = AuthManager(self.conn)
        if data.get("id"):
            sets = "nom=%s, email=%s, role_id=%s, updated_by=%s, updated_at=NOW(), version=version+1"
            vals = [data["nom"], data["email"], data["role_id"], self.user["id"], data["id"], data.get("version", 1)]
            if data.get("password"):
                sets += ", password_hash=%s"
                vals.insert(-2, auth.hash_password(data["password"]))
            cur.execute(f"UPDATE utilisateurs SET {sets} WHERE id=%s AND version=%s AND deleted_at IS NULL", vals)
            if cur.rowcount == 0 and data.get("id"):
                self.conn.rollback(); cur.close()
                raise ValueError("Utilisateur modifié par un autre.")
        else:
            uid = str(uuid.uuid4())
            pw = auth.hash_password(data["password"])
            cur.execute("""
                INSERT INTO utilisateurs (id, etablissement_id, nom, email, role_id,
                    password_hash, created_by, updated_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (uid, self.user["etablissement_id"], data["nom"], data["email"],
                  data["role_id"], pw, self.user["id"], self.user["id"]))
        self.conn.commit(); cur.close()

    def _add_user_dialog(self, user=None):
        roles = self._fetch_roles()
        wf = 360
        nom = ft.TextField(label="Nom", value=user["nom"] if user else "", width=wf)
        email = ft.TextField(label="Email", value=user["email"] if user else "", width=wf)
        pw = ft.TextField(label="Mot de passe", password=True, width=wf) if not user else None
        role = ft.Dropdown(
            label="Rôle",
            options=[ft.dropdown.Option(str(r["id"]), r["nom"]) for r in roles],
            value=str(user["role_id"]) if user else None,
            width=wf, border_radius=ds.SHAPE_XS.radius.top_left,
        )
        err = ft.Text("", color=ds.p.error, size=ds.typo.label_small.size)

        def save(e):
            if not nom.value.strip() or not email.value.strip():
                err.value = "Nom et email requis"; err.update(); return
            if not user and not pw.value:
                err.value = "Mot de passe requis"; err.update(); return
            d = {"id": str(user["id"]) if user else None, "nom": nom.value.strip(), "email": email.value.strip(),
                 "role_id": role.value, "password": pw.value if pw else None}
            if user: d["version"] = user["version"]
            try: self._save_user(d); dlg.open = False; self.page.update(); self._navigate("users")
            except ValueError as e: err.value = str(e); err.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Modifier" if user else "Ajouter"),
            content=ft.Column([n for n in [nom, email, pw, role, err] if n], height=300, spacing=ds.space_sm),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: setattr(dlg,'open',False) or self.page.update()),
                ft.FilledButton(content=ft.Text("Enregistrer"), icon=ft.Icons.SAVE, on_click=save),
            ],
        )
        self.page.show_dialog(dlg)

    def _gen_activation(self, user):
        code, url = self.auth.generate_activation(self.user["id"], str(user["id"]))
        dlg = ft.AlertDialog(
            title=ft.Text(f"Activation : {user['nom']}"),
            content=ft.Column([
                ft.Text("Code d'activation :", size=11),
                ft.Text(code, size=24, weight=ft.FontWeight.BOLD, color=ds.p.primary, text_align=ft.TextAlign.CENTER),
                ft.Text("URL QR :", size=11),
                ft.Text(url, size=11, color=ds.p.text_soft),
                ft.Text("Valable 30 minutes, 3 tentatives max.", size=10, color=ds.p.text_soft),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )
        self.page.show_dialog(dlg)

    def _revoke_device(self, device):
        dlg = ft.AlertDialog(
            title=ft.Text("Revoquer"),
            content=ft.Text(f"Revoquer l'acces de {device.get('device_name', 'cet appareil')} ?"),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: setattr(dlg,'open',False) or self.page.update()),
                ft.FilledButton(content=ft.Text("Revoquer"), icon=ft.Icons.BLOCK,
                               on_click=lambda e: (
                                   self.auth.revoke_device(str(device["id"]), self.user["id"]),
                                   setattr(dlg, 'open', False), self.page.update(),
                                   self._navigate("users"))),
            ],
        )
        self.page.show_dialog(dlg)

    def _users_content(self):
        users = self._fetch_users()
        devices = self.auth.list_devices(self.user["etablissement_id"])

        user_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
        device_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

        for u in users:
            user_list.controls.append(ft.Container(
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=ds.icon_sm, color=ds.p.primary),
                    ft.Column([ft.Text(u["nom"],size=14),ft.Text(u.get("role_nom","-"),size=11,color=ds.p.text_soft)],spacing=0,expand=True),
                    ft.IconButton(icon=ft.Icons.QR_CODE, icon_size=16, tooltip="QR activation", on_click=lambda e,uu=u: self._gen_activation(uu)),
                    ft.IconButton(icon=ft.Icons.EDIT, icon_size=16, tooltip="Modifier", on_click=lambda e,uu=u: self._add_user_dialog(uu)),
                ]),
                padding=ft.Padding(ds.space_sm,ds.space_xs,ds.space_sm,ds.space_xs),
                border=ft.Border(bottom=ft.BorderSide(1,ds.p.outline_variant)),
            ))

        for d in devices:
            device_list.controls.append(ft.Container(
                ft.Row([
                    ft.Icon(ft.Icons.PHONE_ANDROID, size=ds.icon_sm, color=ds.p.primary),
                    ft.Column([ft.Text(d.get("device_name","Appareil"),size=12),ft.Text(f"{d.get('utilisateur_nom','')} - {d.get('device_ip','')}",size=10,color=ds.p.text_soft)],spacing=0,expand=True),
                    ft.IconButton(icon=ft.Icons.BLOCK, icon_size=16, icon_color=ds.p.error, tooltip="Revoquer", on_click=lambda e,dd=d: self._revoke_device(dd)),
                ]),
                padding=ft.Padding(ds.space_sm,ds.space_xs,ds.space_sm,ds.space_xs),
                border=ft.Border(bottom=ft.BorderSide(1,ds.p.outline_variant)),
            ))

        left = ft.Container(ft.Column([
            ft.Row([ft.Text("Utilisateurs",size=16,weight=ft.FontWeight.BOLD,expand=True),
                    ft.IconButton(icon=ft.Icons.ADD, icon_size=18, tooltip="Ajouter", on_click=lambda e: self._add_user_dialog())]),
            user_list,
        ]), width=350, bgcolor=ds.p.background, padding=ft.Padding(ds.space_md,0,ds.space_md,ds.space_md),
           border=ft.Border(right=ft.BorderSide(1,ds.p.outline_variant)))

        right = ft.Container(ft.Column([
            ft.Text("Appareils connectes",size=16,weight=ft.FontWeight.BOLD),
            device_list if device_list.controls else ft.Text("Aucun appareil appaire.",size=12,color=ds.p.text_soft,italic=True),
        ]), expand=True, bgcolor=ds.p.background, padding=ft.Padding(ds.space_md,0,ds.space_md,ds.space_md))

        return ft.Row([left, right], expand=True, spacing=0)



    # ══════════════════════════════════════════════════
    #  Profil Établissement + Pages + Apparence
    # ══════════════════════════════════════════════════

    _etab_tab = "profil"

    def _etablissement_content(self):
        tab_bar = ft.Row(spacing=0)
        for k, lbl, ico in [("profil","Profil",ft.Icons.STOREFRONT),("pages","Pages",ft.Icons.DESCRIPTION),("apparence","Apparence",ft.Icons.PALETTE)]:
            sel = self._etab_tab == k
            tab_bar.controls.append(ft.Container(ft.Text(lbl,size=13,weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL,color=ds.p.on_primary if sel else ds.p.primary),padding=ft.Padding(ds.space_md,ds.space_sm,ds.space_md,ds.space_sm),bgcolor=ds.p.primary if sel else None,border=ft.Border(bottom=ft.BorderSide(2,ds.p.primary) if sel else ft.BorderSide(0,ft.Colors.TRANSPARENT)),on_click=lambda e,kk=k:self._switch_etab_tab(kk)))

        if self._etab_tab == "profil": body = self._etab_profil_content()
        elif self._etab_tab == "pages": body = self._pages_content()
        else: body = self._apparence_content()
        return ft.Column([tab_bar, spacer(ds.space_sm), body], expand=True)

    def _switch_etab_tab(self, tab):
        self._etab_tab = tab; self._navigate("etablissement")

    def _etab_profil_content(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM etablissements WHERE id=%s AND deleted_at IS NULL",(self.user["etablissement_id"],)); e = cur.fetchone(); cur.close()
        wf = 500
        def val(k,d=""): return (e.get(k) or d) if e else d
        nom = ft.TextField(label="Nom",value=val("nom"),width=wf)
        typ = ft.Dropdown(label="Type",options=[ft.dropdown.Option(t,t) for t in ("restaurant","boutique_reelle","boutique_virtuelle")],value=val("type","restaurant"),width=wf)
        hist = ft.TextField(label="Historique",value=val("historique"),width=wf,multiline=True,min_lines=2,max_lines=5)
        mission = ft.TextField(label="Mission",value=val("mission"),width=wf,multiline=True,min_lines=2,max_lines=5)
        adr = ft.TextField(label="Adresse",value=val("adresse"),width=wf)
        tel = ft.TextField(label="Telephone",value=val("telephone"),width=wf)
        email = ft.TextField(label="Email",value=val("email"),width=wf)
        site = ft.TextField(label="Site web",value=val("site_web"),width=wf)
        paiements = ft.TextField(label="Moyens paiement",value=val("moyens_paiement_acceptes"),width=wf)
        tva = ft.TextField(label="TVA defaut (%)",value=str(val("taux_tva_defaut",0)),width=wf)
        logo_url = ft.TextField(label="Logo (nom fichier)",value=val("logo_url"),width=wf)
        err = ft.Text("",color=ds.p.error,size=11); ok = ft.Text("",color=ds.p.success,size=11)
        def save(e):
            try:
                cur2 = self.conn.cursor()
                cur2.execute("""UPDATE etablissements SET nom=%s,type=%s,historique=%s,mission=%s,adresse=%s,telephone=%s,email=%s,site_web=%s,moyens_paiement_acceptes=%s,taux_tva_defaut=%s,logo_url=%s,updated_by=%s,updated_at=NOW(),version=version+1 WHERE id=%s AND version=%s AND deleted_at IS NULL""",
                    (nom.value.strip(),typ.value,hist.value.strip(),mission.value.strip(),adr.value.strip(),tel.value.strip(),email.value.strip(),site.value.strip(),paiements.value.strip(),float(tva.value or 0),(logo_url.value or "").strip(),self.user["id"],self.user["etablissement_id"],val("version",1)))
                if cur2.rowcount == 0: self.conn.rollback(); err.value = "Modifie par un autre"
                else: self.conn.commit(); err.value = ""; ok.value = "Enregistre"; self.user["etablissement_nom"] = nom.value.strip()
                err.update(); ok.update(); cur2.close()
            except Exception as ex: self.conn.rollback(); err.value = str(ex); err.update()
        return ft.Column([ft.Text("Profil",size=22,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),ft.FilledButton(content=ft.Text("Enregistrer"),icon=ft.Icons.SAVE,on_click=save),spacer(ds.space_md),ft.Row([ft.Column([ft.Text("General",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),logo_url,spacer(ds.space_sm),nom,spacer(ds.space_sm),typ,spacer(ds.space_lg),ft.Text("Storytelling",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),hist,spacer(ds.space_lg),ft.Text("Config",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),paiements,spacer(ds.space_sm),tva],expand=1),spacer(ds.space_lg),ft.Column([ft.Text("Contact",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),adr,spacer(ds.space_sm),tel,spacer(ds.space_sm),email,spacer(ds.space_sm),site,spacer(ds.space_lg),ft.Text("Mission & Valeurs",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),mission],expand=1)],vertical_alignment=ft.CrossAxisAlignment.START),spacer(ds.space_sm),ft.Row([err,ok])])

    # ═══════ Pages ═══════
    def _fetch_pages(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cur.execute("SELECT * FROM pages WHERE etablissement_id=%s AND deleted_at IS NULL ORDER BY ordre",(self.user["etablissement_id"],)); return [dict(r) for r in cur.fetchall()]
        except: cur.execute("SELECT * FROM pages_etablissement WHERE etablissement_id=%s AND deleted_at IS NULL ORDER BY ordre",(self.user["etablissement_id"],)); return [dict(r) for r in cur.fetchall()]

    def _save_page(self, data):
        cur = self.conn.cursor(); eid = self.user["etablissement_id"]; uid = self.user["id"]
        try:
            if data.get("id"): cur.execute("UPDATE pages SET titre=%s,contenu=%s,ordre=%s,updated_by=%s,updated_at=NOW(),version=version+1 WHERE id=%s AND version=%s",(data["titre"],data.get("contenu",""),data.get("ordre",0),uid,data["id"],data.get("version",1)))
            else: cur.execute("INSERT INTO pages (id,etablissement_id,titre,slug,contenu,ordre,created_by,updated_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(str(uuid.uuid4()),eid,data["titre"],data.get("slug",""),data.get("contenu",""),data.get("ordre",0),uid,uid))
        except:  # pages_etablissement table
            if data.get("id"): cur.execute("UPDATE pages_etablissement SET titre=%s,contenu_html=%s,ordre=%s,updated_by=%s,updated_at=NOW(),version=version+1 WHERE id=%s AND version=%s",(data["titre"],data.get("contenu",""),data.get("ordre",0),uid,data["id"],data.get("version",1)))
            else: cur.execute("INSERT INTO pages_etablissement (id,etablissement_id,numero_page,titre,contenu_html,ordre,created_by,updated_by,est_active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(str(uuid.uuid4()),eid,int(data.get("numero_page",1)),data["titre"],data.get("contenu",""),data.get("ordre",0),uid,uid,True))
        self.conn.commit(); cur.close()

    def _delete_page(self, pid):
        cur = self.conn.cursor()
        try: cur.execute("UPDATE pages SET deleted_at=NOW() WHERE id=%s",(pid,))
        except: cur.execute("UPDATE pages_etablissement SET deleted_at=NOW() WHERE id=%s",(pid,))
        self.conn.commit(); cur.close()

    def _pages_content(self):
        pages = self._fetch_pages(); plist = ft.Column(spacing=ds.space_sm,expand=True)
        for p in pages:
            plist.controls.append(ft.Container(ft.Row([ft.Text(p.get("titre",""),size=14,expand=True),ft.IconButton(icon=ft.Icons.EDIT,icon_size=16,on_click=lambda e,pp=p:self._page_editor_dialog(pp)),ft.IconButton(icon=ft.Icons.DELETE,icon_size=16,icon_color=ds.p.error,on_click=lambda e,pp=p:self._page_delete_confirm(pp))]),padding=ds.space_md,border=ft.Border(bottom=ft.BorderSide(1,ds.p.outline_variant))))
        return ft.Column([ft.Row([ft.Text("Pages de l'etablissement",size=18,weight=ft.FontWeight.BOLD,expand=True),ft.IconButton(icon=ft.Icons.ADD,icon_size=18,on_click=lambda e:self._page_editor_dialog())]),spacer(ds.space_sm),plist],expand=True)

    def _page_editor_dialog(self, page=None):
        t = ft.TextField(label="Titre",value=page["titre"] if page else "",width=400)
        c = ft.TextField(label="Contenu (Markdown)",value=page.get("contenu","") if page else "",width=400,multiline=True,min_lines=4,max_lines=12)
        err = ft.Text("",color=ds.p.error,size=11)
        def save(e):
            if not t.value.strip(): err.value="Titre requis";err.update();return
            d={"id":page["id"] if page else None,"titre":t.value.strip(),"contenu":c.value,"ordre":page.get("ordre",0) if page else 99}
            if page: d["version"]=page.get("version",1)
            try: self._save_page(d);dlg.open=False;self.page.update();self._navigate("etablissement")
            except Exception as ex: err.value=str(ex);err.update()
        dlg = ft.AlertDialog(title=ft.Text("Editer" if page else "Ajouter une page"),content=ft.Column([t,c,err],width=440),actions=[ft.TextButton("Annuler",on_click=lambda e:setattr(dlg,'open',False) or self.page.update()),ft.FilledButton(content=ft.Text("Enregistrer"),icon=ft.Icons.SAVE,on_click=save)])
        self.page.show_dialog(dlg)

    def _page_delete_confirm(self, page):
        def do_del(e): self._delete_page(page["id"]);dlg.open=False;self.page.update();self._navigate("etablissement")
        dlg = ft.AlertDialog(title=ft.Text("Confirmer"),content=ft.Text(f"Supprimer '{page.get('titre','')}' ?"),actions=[ft.TextButton("Annuler",on_click=lambda e:setattr(dlg,'open',False) or self.page.update()),ft.FilledButton(content=ft.Text("Supprimer"),icon=ft.Icons.DELETE,on_click=do_del)])
        self.page.show_dialog(dlg)

    # ═══════ Theme / Apparence ═══════
    def _fetch_theme_presets(self):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor); cur.execute("SELECT * FROM theme_presets ORDER BY theme_id"); rows = [dict(r) for r in cur.fetchall()]; cur.close(); return rows
        except: return []

    def _fetch_theme_config(self):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor); cur.execute("SELECT * FROM theme_config WHERE etablissement_id=%s",(self.user["etablissement_id"],)); r = cur.fetchone(); cur.close(); return dict(r) if r else {}
        except: return {}

    def _save_theme_config(self, data):
        tc = self._fetch_theme_config(); cur = self.conn.cursor()
        if tc and tc.get("id"): cur.execute("""UPDATE theme_config SET theme_id=%s,primary_color=%s,secondary_color=%s,accent_color=%s,surface_color=%s,font_heading=%s,hero_title=%s,hero_subtitle=%s,hero_button_text=%s,hero_image_url=%s,seo_title_template=%s,seo_description=%s,facebook_url=%s,instagram_url=%s,whatsapp_number=%s,footer_text=%s,custom_css=%s,version=version+1,updated_at=NOW() WHERE id=%s""",(data["theme_id"],data["primary_color"],data["secondary_color"],data["accent_color"],data["surface_color"],data["font_heading"],data["hero_title"],data["hero_subtitle"],data["hero_button_text"],data["hero_image_url"],data["seo_title_template"],data["seo_description"],data["facebook_url"],data["instagram_url"],data["whatsapp_number"],data["footer_text"],data["custom_css"],tc["id"]))
        else: cur.execute("INSERT INTO theme_config (id,etablissement_id,theme_id,primary_color,secondary_color,accent_color,surface_color,font_heading,hero_title,hero_subtitle,hero_button_text,hero_image_url,seo_title_template,seo_description,facebook_url,instagram_url,whatsapp_number,footer_text,custom_css,version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(str(uuid.uuid4()),self.user["etablissement_id"],data["theme_id"],data["primary_color"],data["secondary_color"],data["accent_color"],data["surface_color"],data["font_heading"],data["hero_title"],data["hero_subtitle"],data["hero_button_text"],data["hero_image_url"],data["seo_title_template"],data["seo_description"],data["facebook_url"],data["instagram_url"],data["whatsapp_number"],data["footer_text"],data["custom_css"],1))
        self.conn.commit(); cur.close()

    def _apparence_content(self):
        tc = self._fetch_theme_config(); presets = self._fetch_theme_presets(); wf = 480
        preset_opts = [ft.dropdown.Option(p["theme_id"],p["theme_name"]) for p in presets]
        preset_dd = ft.Dropdown(label="Template",options=preset_opts,value=tc.get("theme_id",""),width=wf)
        primary = ft.TextField(label="Principale hex",value=tc.get("primary_color","#1565C0"),width=wf)
        secondary = ft.TextField(label="Secondaire hex",value=tc.get("secondary_color","#00897B"),width=wf)
        accent = ft.TextField(label="Accent hex",value=tc.get("accent_color","#E65100"),width=wf)
        surf = ft.TextField(label="Surface hex",value=tc.get("surface_color","#F5F7FA"),width=wf)
        font = ft.TextField(label="Police",value=tc.get("font_heading","Inter"),width=wf)
        hero_title = ft.TextField(label="Titre Hero",value=tc.get("hero_title",""),width=wf)
        hero_sub = ft.TextField(label="Sous-titre Hero",value=tc.get("hero_subtitle",""),width=wf,multiline=True,min_lines=2,max_lines=4)
        hero_btn = ft.TextField(label="Bouton Hero",value=tc.get("hero_button_text",""),width=wf)
        hero_img = ft.TextField(label="Image Hero (fichier)",value=tc.get("hero_image_url",""),width=wf)
        seo_title = ft.TextField(label="Template titre SEO",value=tc.get("seo_title_template",""),width=wf)
        seo_desc = ft.TextField(label="Description SEO",value=tc.get("seo_description",""),width=wf,multiline=True,min_lines=2,max_lines=4)
        fb = ft.TextField(label="Facebook URL",value=tc.get("facebook_url",""),width=wf)
        insta = ft.TextField(label="Instagram URL",value=tc.get("instagram_url",""),width=wf)
        wa = ft.TextField(label="WhatsApp",value=tc.get("whatsapp_number",""),width=wf)
        footer_txt = ft.TextField(label="Footer",value=tc.get("footer_text",""),width=wf)
        css_txt = ft.TextField(label="CSS custom",value=tc.get("custom_css",""),width=wf,multiline=True,min_lines=4,max_lines=10)
        err = ft.Text("",color=ds.p.error,size=11); ok = ft.Text("",color=ds.p.success,size=11)

        def apply_preset(e):
            pid = preset_dd.value; p = next((x for x in presets if x["theme_id"]==pid),None)
            if not p: return
            for f,kk in [(primary,"primary_color"),(secondary,"secondary_color"),(accent,"accent_color"),(surf,"surface_color"),(font,"font_heading"),(hero_title,"hero_title"),(hero_sub,"hero_subtitle"),(css_txt,"custom_css")]: f.value=p.get(kk,""); f.update()
        preset_dd.on_change = apply_preset

        def save(e):
            try:
                d={"theme_id":preset_dd.value or "artizboard","primary_color":primary.value.strip(),"secondary_color":secondary.value.strip(),"accent_color":accent.value.strip(),"surface_color":surf.value.strip(),"font_heading":font.value.strip(),"hero_title":hero_title.value.strip(),"hero_subtitle":hero_sub.value.strip(),"hero_button_text":hero_btn.value.strip(),"hero_image_url":hero_img.value.strip(),"seo_title_template":seo_title.value.strip(),"seo_description":seo_desc.value.strip(),"facebook_url":fb.value.strip(),"instagram_url":insta.value.strip(),"whatsapp_number":wa.value.strip(),"footer_text":footer_txt.value.strip(),"custom_css":css_txt.value}
                self._save_theme_config(d);err.value="";ok.value="Enregistre";ok.update()
            except Exception as ex: err.value=str(ex);err.update()

        return ft.Column([ft.Text("Apparence",size=22,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),ft.FilledButton(content=ft.Text("Enregistrer"),icon=ft.Icons.SAVE,on_click=save),spacer(ds.space_md),preset_dd,spacer(ds.space_md),ft.Text("Couleurs",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),ft.Row([primary,spacer(ds.space_sm),secondary]),spacer(ds.space_sm),ft.Row([accent,spacer(ds.space_sm),surf]),spacer(ds.space_sm),font,spacer(ds.space_lg),ft.Text("Hero",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),hero_title,spacer(ds.space_sm),hero_sub,spacer(ds.space_sm),hero_btn,spacer(ds.space_sm),hero_img,spacer(ds.space_lg),ft.Text("SEO",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),seo_title,spacer(ds.space_sm),seo_desc,spacer(ds.space_lg),ft.Text("Reseaux",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),fb,spacer(ds.space_sm),insta,spacer(ds.space_sm),wa,spacer(ds.space_lg),ft.Text("Footer & CSS",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),footer_txt,spacer(ds.space_sm),css_txt,spacer(ds.space_sm),ft.Row([err,ok])],expand=True,scroll=ft.ScrollMode.AUTO)

    # ══════════════════════════════════════════════════
    #  Commandes
    # ══════════════════════════════════════════════════

    def _fetch_commandes(self, statut=""):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        q = "SELECT c.*, u.nom AS client_nom, s.nom AS staff_nom FROM commandes c LEFT JOIN utilisateurs u ON c.client_id=u.id AND u.deleted_at IS NULL LEFT JOIN utilisateurs s ON c.staff_id=s.id AND s.deleted_at IS NULL WHERE c.etablissement_id=%s AND c.deleted_at IS NULL"
        params=[self.user["etablissement_id"]]
        if statut: q+=" AND c.statut=%s"; params.append(statut)
        cur.execute(q+" ORDER BY c.created_at DESC LIMIT 50",tuple(params)); rows=[dict(r) for r in cur.fetchall()]; cur.close(); return rows

    def _fetch_lignes(self, cid):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT lc.*, p.nom AS produit_nom FROM lignes_commande lc JOIN produits p ON lc.produit_id=p.id WHERE lc.commande_id=%s AND lc.deleted_at IS NULL",(cid,))
        rows=[dict(r) for r in cur.fetchall()]; cur.close(); return rows

    def _change_statut(self, cid, ns):
        cur=self.conn.cursor(); cur.execute("UPDATE commandes SET statut=%s,updated_by=%s,updated_at=NOW() WHERE id=%s",(ns,self.user["id"],cid)); self.conn.commit(); cur.close()

    def _commandes_content(self):
        self._cmdsel=None; self._cmdfilter=""
        cmd_list=ft.Column(scroll=ft.ScrollMode.AUTO,expand=True,spacing=0)
        detail_panel=ft.Container(ft.Column([ft.Icon(ft.Icons.RECEIPT_LONG,size=48,color=ds.p.text_disabled,opacity=0.5),ft.Text("Selectionnez une commande",size=12,color=ds.p.text_soft,italic=True)],alignment=ft.MainAxisAlignment.CENTER,horizontal_alignment=ft.CrossAxisAlignment.CENTER),expand=True,bgcolor=ds.p.surface_variant,border_radius=ds.SHAPE_MD.radius.top_left,padding=ds.space_md)
        statuses=["","en_attente","en_preparation","pret","livre","annule"]; labels={"":"Toutes","en_attente":"En attente","en_preparation":"En prep","pret":"Pretes","livre":"Livrees","annule":"Annulees"}
        colors={"":ds.p.text_soft,"en_attente":"#E65100","en_preparation":"#1565C0","pret":"#2E7D32","livre":"#546E7A","annule":"#C62828"}
        chip_row=ft.Row(spacing=ds.space_xs,wrap=True)
        for s in statuses: sel=self._cmdfilter==s; chip_row.controls.append(ft.Container(ft.Text(labels[s],size=11,color=ds.p.on_primary if sel else colors[s],weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL),padding=ft.Padding(ds.space_sm,ds.space_xs,ds.space_sm,ds.space_xs),bgcolor=colors[s] if sel else None,border=ft.Border.all(1,colors[s]) if not sel else None,border_radius=ds.SHAPE_FULL.radius.top_left,on_click=lambda e,ss=s:self._filter_cmd(ss)))
        statut_icons={"en_attente":("pending",ds.p.tertiary),"en_preparation":("cooking",ds.p.primary),"pret":("check_circle",ds.p.success),"livre":("local_shipping",ds.p.text_soft),"annule":("cancel",ds.p.error)}
        paiement_labels={"cash":"Especes","tmoney":"TMoney","flooz":"Flooz","mixte":"Mixte"}
        statut_labels={"en_attente":"En attente","en_preparation":"En prep","pret":"Prete","livre":"Livree","annule":"Annulee"}
        def refresh_cmds():
            cmd_list.controls.clear(); cmds=self._fetch_commandes(self._cmdfilter)
            for c in cmds:
                cid=str(c["id"]); is_sel=cid==self._cmdsel; st=c["statut"] or "en_attente"
                icon,_=statut_icons.get(st,("help",ds.p.text_soft))
                date_str=str(c.get("created_at",""))[:10]
                client=c.get("client_nom") or c.get("reference_client") or "Comptoir"
                cmd_list.controls.append(ft.Container(ft.Row([ft.Icon(icon,size=16,color=_),ft.Column([ft.Text(f"{client} - {date_str}",size=13,weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL),ft.Text(f"{float(c['total']):,.0f}F  {paiement_labels.get(c.get('moyen_paiement',''),'-')}  {statut_labels.get(st,st)}",size=10,color=ds.p.text_soft)],spacing=0,expand=True)]),padding=ft.Padding(ds.space_sm,ds.space_xs,ds.space_sm,ds.space_xs),bgcolor=ds.p.primary_container if is_sel else None,border_radius=ds.SHAPE_XS.radius.top_left,on_click=lambda e,cc=c:self.select_cmd(cc)))
            try:cmd_list.update()
            except RuntimeError:pass
        def refresh_detail():
            if not self._cmdsel: detail_panel.content=ft.Column([ft.Icon(ft.Icons.RECEIPT_LONG,size=48,color=ds.p.text_disabled,opacity=0.5),ft.Text("Selectionnez",size=12,color=ds.p.text_soft,italic=True)],alignment=ft.MainAxisAlignment.CENTER,horizontal_alignment=ft.CrossAxisAlignment.CENTER); detail_panel.bgcolor=ds.p.surface_variant
            else:
                cur=self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor); cur.execute("SELECT c.*,u.nom AS client_nom,s.nom AS staff_nom FROM commandes c LEFT JOIN utilisateurs u ON c.client_id=u.id LEFT JOIN utilisateurs s ON c.staff_id=s.id WHERE c.id=%s AND c.deleted_at IS NULL",(self._cmdsel,)); cmd=cur.fetchone(); cur.close()
                if not cmd: return
                lignes=self._fetch_lignes(self._cmdsel); st=cmd["statut"] or "en_attente"; _,sc=statut_icons.get(st,("help",ds.p.text_soft))
                items_col=ft.Column(spacing=ds.space_xxs)
                for lc in lignes: items_col.controls.append(ft.Row([ft.Text(lc.get("produit_nom","-"),size=12,expand=True),ft.Text(f"{int(lc['quantite'])}x{float(lc['prix_unitaire']):,.0f}",size=12)]))
                next_statuses={"en_attente":"en_preparation","en_preparation":"pret","pret":"livre"}; ns=next_statuses.get(st)
                detail_panel.bgcolor=ds.p.background
                detail_panel.content=ft.Column([ft.Row([ft.Text(f"Cmd {str(cmd['id'])[:8]}...",size=16,weight=ft.FontWeight.BOLD),ft.Container(ft.Text(statut_labels.get(st,st),size=10,color=ds.p.on_primary),padding=ft.Padding(ds.space_sm,ds.space_xxs,ds.space_sm,ds.space_xxs),bgcolor=sc,border_radius=ds.SHAPE_FULL.radius.top_left)]),spacer(ds.space_sm),ft.Row([ft.Text(f"Client: {cmd.get('client_nom') or cmd.get('reference_client') or 'Comptoir'}",size=11,color=ds.p.text_soft),ft.Text(f"Staff: {cmd.get('staff_nom') or '-'}",size=11,color=ds.p.text_soft)]),spacer(ds.space_sm),ft.Text(f"Total: {float(cmd['total']):,.0f}F | Paiement: {paiement_labels.get(cmd.get('moyen_paiement',''),'-')} | {cmd.get('type_service','sur_place')}",size=11,color=ds.p.text_soft),spacer(ds.space_sm),ft.Divider(height=1,color=ds.p.outline_variant),spacer(ds.space_sm),items_col,spacer(ds.space_md),ft.Row([ft.TextButton("Annuler",icon=ft.Icons.CANCEL,on_click=lambda e:self._confirm_annuler(self._cmdsel)) if st not in ("livre","annule") else ft.Container(),ft.Container(expand=True),ft.FilledButton(content=ft.Text(f"->{statut_labels.get(ns,ns)}"),icon=ft.Icons.ARROW_FORWARD,on_click=lambda e:self._do_change_statut(self._cmdsel,ns)) if ns else ft.Container()])],spacing=0)
            try:detail_panel.update()
            except RuntimeError:pass
        def select_cmd(cmd): self._cmdsel=str(cmd["id"]); refresh_cmds(); refresh_detail()
        refresh_cmds()
        left=ft.Container(ft.Column([chip_row,spacer(ds.space_sm),cmd_list]),width=350,bgcolor=ds.p.background,border=ft.Border(right=ft.BorderSide(1,ds.p.outline_variant)))
        right=ft.Container(detail_panel,expand=True,bgcolor=ds.p.background)
        return ft.Column([ft.Text("Commandes",size=22,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),ft.Row([left,right],expand=True,spacing=0)],expand=True)

    def _filter_cmd(self,statut): self._cmdfilter=statut; self._cmdsel=None; self._navigate("commandes")
    def _confirm_annuler(self,cid): self._do_change_statut(cid,"annule")
    def _do_change_statut(self,cid,ns): self._change_statut(cid,ns); self._navigate("commandes")

    # ══════════════════════════════════════════════════
    #  Rapports & Exports
    # ══════════════════════════════════════════════════

    def _rapports_content(self):
        from dashboard_manager import DashboardManager
        dm = DashboardManager(self.conn, self.user["etablissement_id"]); today = datetime.now().strftime("%Y-%m-%d")
        debut_f = ft.TextField(label="Du",value=today,width=130); fin_f = ft.TextField(label="Au",value=today,width=130)
        kpi_container = ft.Row(spacing=ds.space_md); best_col = ft.Column(spacing=ds.space_xs,expand=True); alertes_col = ft.Column(spacing=ds.space_xs,expand=True); ok_msg = ft.Text("",size=11,color=ds.p.success)
        def refresh(e=None):
            d=debut_f.value or today; f=fin_f.value or today; kpis=dm.get_kpis(d,f)
            ca=float(kpis.get("ca_total",0)); nb=int(kpis.get("nb_commandes",0)); pm=float(kpis.get("panier_moyen",0))
            kpi_container.controls.clear()
            for v,l in [(f"{ca:,.0f}F","CA"),(str(nb),"Cmd"),(f"{pm:,.0f}F","Panier")]: kpi_container.controls.append(ft.Container(ft.Column([ft.Text(v,size=20,weight=ft.FontWeight.BOLD,color=ds.p.primary),ft.Text(l,size=11,color=ds.p.text_soft)],spacing=0),padding=ds.space_md,bgcolor=ds.p.primary_container,border_radius=ds.SHAPE_MD.radius.top_left,expand=True))
            best=dm.get_best_sellers(d,f,5); best_col.controls.clear(); best_col.controls.append(ft.Text("Top 5 ventes",size=16,weight=ft.FontWeight.BOLD))
            for i,p in enumerate(best): best_col.controls.append(ft.Text(f"{i+1}. {p['nom']} - {p['total_quantite']}",size=12,color=ds.p.text_soft))
            alertes=dm.get_alertes_rupture(); alertes_col.controls.clear(); alertes_col.controls.append(ft.Text("Alertes stock",size=16,weight=ft.FontWeight.BOLD))
            if alertes:
                for a in alertes: alertes_col.controls.append(ft.Text(f"! {a['nom']}: {a['stock']}/{a['stock_alerte']}",size=12,color=ds.p.error))
            else: alertes_col.controls.append(ft.Text("Aucune",size=12,color=ds.p.text_soft,italic=True))
            try: kpi_container.update();best_col.update();alertes_col.update()
            except RuntimeError: pass
        def export_csv(e):
            try: d=debut_f.value or today; f=fin_f.value or today; p=dm.export_csv_journal_financier(d,f); ok_msg.value=f"CSV: {p.name}"; ok_msg.update()
            except Exception as ex: ok_msg.value=str(ex); ok_msg.update()
        def export_pdf(e):
            try: d=debut_f.value or today; f=fin_f.value or today; p=dm.export_pdf_rapport(d,f); ok_msg.value=f"PDF: {p.name}"; ok_msg.update()
            except Exception as ex: ok_msg.value=str(ex); ok_msg.update()
        refresh()
        return ft.Column([ft.Text("Rapports",size=22,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),ft.Row([debut_f,spacer(ds.space_sm),fin_f,spacer(ds.space_sm),ft.FilledTonalButton(content=ft.Text("Refresh"),icon=ft.Icons.REFRESH,on_click=refresh),spacer(ds.space_sm),ft.FilledTonalButton(content=ft.Text("CSV"),icon=ft.Icons.TABLE_CHART,on_click=export_csv),spacer(ds.space_sm),ft.FilledTonalButton(content=ft.Text("PDF"),icon=ft.Icons.PICTURE_AS_PDF,on_click=export_pdf)]),spacer(ds.space_sm),ok_msg,spacer(ds.space_md),ft.Text("Indicateurs",size=16,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),kpi_container,spacer(ds.space_lg),ft.Row([best_col,spacer(ds.space_lg),alertes_col],expand=True)],expand=True,scroll=ft.ScrollMode.AUTO)

    # ══════════════════════════════════════════════════
    #  Sauvegardes
    # ══════════════════════════════════════════════════

    def _backups_content(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM backups ORDER BY created_at DESC LIMIT 20"); backups=[dict(r) for r in cur.fetchall()]; cur.close()
        blist=ft.Column(scroll=ft.ScrollMode.AUTO,expand=True,spacing=0)
        for b in backups:
            bid=str(b["id"]); date_str=str(b.get("created_at",""))[:19].replace("T"," ")
            taille=f"{float(b.get('taille_bytes',0))/(1024*1024):.1f} Mo"
            blist.controls.append(ft.Container(ft.Row([ft.Icon(ft.Icons.ARCHIVE,size=ds.icon_sm,color=ds.p.primary),ft.Column([ft.Text(b["filename"],size=14),ft.Text(f"{date_str} - {taille} - {b.get('type','manuel')}",size=11,color=ds.p.text_soft)],spacing=0,expand=True),ft.TextButton("Restaurer",on_click=lambda e,bb=bid:self._restore_backup(bb))]),padding=10,border=ft.Border(bottom=ft.BorderSide(1,ds.p.outline_variant))))
        def do_backup(e):
            try: self._perform_backup(); self._navigate("sauvegardes")
            except Exception as ex: import traceback; traceback.print_exc()
        return ft.Column([ft.Text("Sauvegardes",size=22,weight=ft.FontWeight.BOLD),spacer(ds.space_sm),ft.FilledButton(content=ft.Text("Sauvegarder maintenant"),icon=ft.Icons.BACKUP,on_click=do_backup),spacer(ds.space_md),ft.Text("Existantes",size=16,weight=ft.FontWeight.BOLD),blist if backups else ft.Text("Aucune sauvegarde.",size=12,color=ds.p.text_soft,italic=True)],expand=True)

    def _perform_backup(self):
        import subprocess,hashlib,gzip,os as _os
        bk_config = {"directory": Path("C:/projet/backups")}
        backup_dir = bk_config["directory"]; backup_dir.mkdir(parents=True,exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S"); filename = f"artizboard_{timestamp}.dump"; filepath = backup_dir / filename; gz_path = filepath.with_suffix(".dump.gz")
        env = _os.environ.copy(); env["PGPASSWORD"] = "artizboard_pass"
        result = subprocess.run(["pg_dump","-h","127.0.0.1","-p","5432","-U","artizboard","-d","artizboard_local","-F","c","-f",str(filepath)],env=env,capture_output=True)
        if result.returncode != 0: raise RuntimeError(f"pg_dump failed: {result.stderr.decode()}")
        with open(filepath,"rb") as f: data=f.read(); checksum=hashlib.sha256(data).hexdigest(); size=len(data)
        with gzip.open(gz_path,"wb") as gzf: gzf.write(data)
        filepath.unlink()
        cur=self.conn.cursor(); cur.execute("INSERT INTO backups (id,filename,checksum_sha256,taille_bytes,type,local_path) VALUES (%s,%s,%s,%s,%s,%s)",(str(uuid.uuid4()),gz_path.name,checksum,size,"manuel",str(gz_path))); self.conn.commit(); cur.close()

    def _restore_backup(self,bid):
        cur=self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor); cur.execute("SELECT * FROM backups WHERE id=%s",(bid,)); b=cur.fetchone(); cur.close()
        if not b: return
        dlg=ft.AlertDialog(title=ft.Text("Confirmer restoration"),content=ft.Text(f"Restaurer '{b['filename']}' ? Ceci ecrasera les donnees actuelles."),actions=[ft.TextButton("Annuler",on_click=lambda e:setattr(dlg,'open',False) or self.page.update()),ft.FilledButton(content=ft.Text("Restaurer"),icon=ft.Icons.RESTORE,on_click=lambda e:(self._do_restore_operation(bid),setattr(dlg,'open',False),self.page.update(),self._navigate("sauvegardes")))])
        self.page.show_dialog(dlg)

    def _do_restore_operation(self,bid):
        import gzip,hashlib,os as _os,tempfile
        cur=self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor); cur.execute("SELECT * FROM backups WHERE id=%s",(bid,)); b=cur.fetchone(); cur.close()
        if not b: raise ValueError("Sauvegarde introuvable")
        local_path=Path(b["local_path"]); gz_path=local_path.with_suffix(".dump.gz")
        with open(gz_path,"rb") as f: data=gzip.decompress(f.read()); actual=hashlib.sha256(data).hexdigest()
        if actual!=b["checksum_sha256"]: raise ValueError(f"Checksum invalide")
        with tempfile.NamedTemporaryFile(delete=False,suffix=".dump") as tmp: tmp.write(data); tmp_path=tmp.name
        env=_os.environ.copy(); env["PGPASSWORD"]="artizboard_pass"
        subprocess.run(["pg_restore","-h","127.0.0.1","-p","5432","-U","artizboard","-d","artizboard_local","-c","-F","c",tmp_path],env=env,check=True)
        _os.unlink(tmp_path)
        cur2=self.conn.cursor(); cur2.execute("UPDATE backups SET verified_at=NOW() WHERE id=%s",(bid,)); self.conn.commit(); cur2.close()


def main(page: ft.Page):
    page.title = "ArtizBoard — Administration"
    page.window.width = int(ds.golden_width(680))
    page.window.height = 680
    page.window.resizable = False
    page.window.maximizable = False
    page.padding = 0
    try:
        import tkinter as tk
        root = tk.Tk(); sw, sh = root.winfo_screenwidth(), root.winfo_screenheight(); root.destroy()
        page.window.left = (sw - page.window.width) // 2
        page.window.top = (sh - page.window.height) // 2
    except: pass
    app = AdminApp(page)
    app.run()


if __name__ == "__main__":
    ft.app(target=main)
