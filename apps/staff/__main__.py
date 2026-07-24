"""ArtizBoard — App Staff (Restaurant) v2
python -m apps.staff

3 onglets : Commander | En cours | Encaisser
"""
import flet as ft, io, base64, psycopg2, psycopg2.extras, uuid, sys, threading, time
from pathlib import Path
from datetime import datetime, timezone
from collections import OrderedDict
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ArtizBoardCommon import ds
from ArtizBoardCommon.debug import safe_handler, set_debug
from ArtizBoardCommon.config_loader import get_db_config
from ArtizBoardCommon.components import (
    button, textfield, spacer, divider, headline, body, label,
    ButtonVariant, CardVariant,
)
from apps.common.auth import AuthManager

db = get_db_config()

def _conn():
    return psycopg2.connect(host=db[0], port=db[1], dbname=db[2],
                            user=db[3], password=db[4], client_encoding="UTF8")

class StaffApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.conn = _conn()
        self.auth = AuthManager(self.conn)
        self.user = None
        self._polling = False
        self._pending_new = 0
        self._tab = 0
        self._cart = []
        self._table = "T1"
        self._tables = ["T1","T2","T3","T4","T5","T6","Comptoir"]
        self._file_picker = ft.FilePicker()
        self._file_picker.on_result = self._on_file_picked
        self._scan_target_field = None

    def run(self):
        ds.apply(self.page)
        self.page.bgcolor = ds.p.background
        self.page.padding = 0
        self.page.overlay.append(self._file_picker)
        self._show_login()

    # ═══════════ LOGIN ═══════════
    def _show_login(self, error=""):
        self.page.controls.clear()
        code_field = textfield(label="Code d'activation", hint="8 caracteres", expand=True)
        err = ft.Text(error, color=ds.p.error, size=ds.typo.label_small.size)
        def submit(e):
            token = code_field.value.strip()
            if len(token) < 8: err.value = "8 caracteres requis"; err.update(); return
            try:
                self.conn = _conn(); self.auth = AuthManager(self.conn)
                access, refresh, info = self.auth.activate_device(token, "Staff", "192.168.1.50")
                self.user = info; self.user["token"] = access
                self._show_main()
            except Exception as ex:
                import traceback; traceback.print_exc()
                err.value = f"Echec : {ex}"; err.update()
        self.page.add(
            ft.Column([
                ft.Container(expand=True),
                ft.Container(ft.Column([
                    ft.Icon(ft.Icons.QR_CODE_SCANNER, size=48, color=ds.p.primary),
                    spacer(ds.space_sm), headline("ArtizBoard Staff", size="small"),
                    spacer(ds.space_xxs),
                    body("Scannez le QR code administrateur", size="small", color=ds.p.text_soft),
                    spacer(ds.space_md),
                    ft.Row([
                        code_field,
                        ft.IconButton(
                            icon=ft.Icons.CAMERA_ALT,
                            icon_color=ds.p.primary,
                            icon_size=24,
                            tooltip="Scanner le QR code",
                            on_click=safe_handler(lambda e: self._open_camera(code_field), "Staff.login.scan_qr"),
                        ),
                    ], spacing=ds.space_xs),
                    spacer(ds.space_sm),
                    button("Activer", variant=ButtonVariant.FILLED, icon=ft.Icons.LOGIN, on_click=safe_handler(submit, "Staff.login.submit"), expand=True),
                    spacer(ds.space_sm), err,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=ds.space_xl),
                ft.Container(expand=True),
                ft.Text("\u00a9 2026 ArtizBoard \u00b7 Licence MIT", size=10, color=ds.p.text_disabled),
                spacer(ds.space_sm),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

    def _open_camera(self, code_field):
        """Ouvre le FilePicker pour capturer/selectionner une image de QR code."""
        self._scan_target_field = code_field
        try:
            self._file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE,
                allowed_extensions=["png", "jpg", "jpeg", "bmp"],
            )
        except Exception:
            self._show_snack("Camera non disponible, saisissez le code manuellement",
                             ds.p.error)

    def _on_file_picked(self, e):
        if e.files and len(e.files) > 0:
            self._process_qr(e.files[0].path)

    def _process_qr(self, file_path):
        """D\u00e9code le QR code depuis l'image capturee (placeholder pour l'integration pyzbar)."""
        if not file_path:
            return
        try:
            with open(file_path, "rb") as f:
                img_data = f.read()
            b64_preview = base64.b64encode(img_data[:1024]).decode("utf-8")

            # TODO: Integration pyzbar pour le decodage reel du QR code
            # from pyzbar.pyzbar import decode
            # from PIL import Image
            # img = Image.open(file_path)
            # results = decode(img)
            # if results:
            #     code = results[0].data.decode("utf-8")
            #     if self._scan_target_field:
            #         self._scan_target_field.value = code
            #         self._scan_target_field.update()
            #     self._show_snack("QR code scanne avec succes", ds.p.success)
            #     return

            self._show_snack(
                "Image capturee. Installez pyzbar pour le decodage automatique du QR.",
                ds.p.surface,
            )
        except Exception as ex:
            self._show_snack(f"Erreur de capture : {ex}", ds.p.error)

    def _show_snack(self, message, bgcolor):
        """Affiche un snackbar avec le message donne."""
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=bgcolor,
            duration=4000,
        )
        self.page.snack_bar.open = True
        self.page.update()

    # ═══════════ MAIN ═══════════
    def _show_main(self):
        self.page.controls.clear()
        self._build_tabs()
        content = self._build_content()
        self.page.add(self.tab_bar, content)
        self.page.update()
        if not self._polling:
            self._start_polling()

    def _start_polling(self):
        self._polling = True
        def _poll():
            while self._polling:
                time.sleep(5)
                try:
                    conn = _conn()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT COUNT(*) FROM commandes
                        WHERE etablissement_id=%s AND statut='en_attente'
                        AND created_at > NOW() - INTERVAL '1 minute'
                    """, (self.user["etablissement_id"],))
                    count = cur.fetchone()[0]
                    cur.close()
                    conn.close()
                    if count > self._pending_new:
                        try:
                            import winsound
                            winsound.Beep(1000, 200)
                        except (ImportError, AttributeError):
                            print('\a')
                    self._pending_new = count
                    self.page.run_thread_safe(self._update_badges)
                except Exception:
                    pass
        threading.Thread(target=_poll, daemon=True).start()

    def _stop_polling(self):
        self._polling = False

    def _update_badges(self):
        show = self._pending_new > 0
        if hasattr(self, '_badge_en_cours') and self._badge_en_cours:
            self._badge_en_cours.content.value = str(self._pending_new)
            self._badge_en_cours.visible = show
            self._badge_en_cours.update()
        if hasattr(self, '_badge_kds') and self._badge_kds:
            self._badge_kds.content.value = str(self._pending_new)
            self._badge_kds.visible = show
            self._badge_kds.update()

    def _build_tabs(self):
        self._badge_en_cours = ft.Container(
            ft.Text(str(self._pending_new), size=9, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=ds.p.error, border_radius=ds.SHAPE_FULL.radius.top_left,
            padding=ft.Padding(ds.space_xxs, 1, ds.space_xxs, 1),
            visible=self._pending_new > 0,
        )
        self._badge_kds = ft.Container(
            ft.Text(str(self._pending_new), size=9, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=ds.p.error, border_radius=ds.SHAPE_FULL.radius.top_left,
            padding=ft.Padding(ds.space_xxs, 1, ds.space_xxs, 1),
            visible=self._pending_new > 0,
        )
        self.tab_bar = ft.Container(
            ft.Row([
                self._tab_btn(0, "Commander", ft.Icons.SHOPPING_CART),
                self._tab_btn(1, "En cours", ft.Icons.RESTAURANT_MENU, badge=self._badge_en_cours),
                self._tab_btn(2, "Encaisser", ft.Icons.PAYMENTS),
                self._tab_btn(3, "Cuisine", ft.Icons.SET_MEAL, badge=self._badge_kds),
            ], spacing=0),
            bgcolor=ds.p.surface,
            border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)),
            padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
        )

    def _tab_btn(self, idx, lbl, icon, badge=None):
        sel = self._tab == idx
        row_controls = [
            ft.Icon(icon, size=ds.icon_sm, color=ds.p.primary if sel else ds.p.text_soft),
            ft.Text(lbl, size=11, color=ds.p.primary if sel else ds.p.text_soft,
                    weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL),
        ]
        if badge:
            row_controls.append(spacer(ds.space_xxs))
            row_controls.append(badge)
        return ft.Container(
            ft.Row(row_controls, spacing=ds.space_xxs),
            padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
            on_click=safe_handler(lambda e, i=idx: self._switch_tab(i), "Staff.tab.switch"),
            expand=True, alignment=ft.alignment.Alignment(0, 0),
        )

    def _switch_tab(self, idx):
        self._tab = idx
        self._show_main()

    def _build_content(self):
        if self._tab == 0: return self._commander_view()
        elif self._tab == 1: return self._en_cours_view()
        elif self._tab == 2: return self._encaisser_view()
        else: return self._kds_view()

    # ═══════════ TAB 0 — COMMANDER ═══════════
    def _commander_view(self):
        conn = _conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.id AS cat_id, c.nom AS cat_nom, p.*
            FROM categories c JOIN produits p ON p.categorie_id = c.id
            WHERE p.etablissement_id=%s AND p.deleted_at IS NULL
            AND c.deleted_at IS NULL AND p.permets_commande=TRUE
            ORDER BY c.nom, p.nom
        """, (self.user["etablissement_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()

        by_cat = OrderedDict()
        for r in rows:
            key = (r["cat_id"], r["cat_nom"])
            if key not in by_cat: by_cat[key] = []
            by_cat[key].append(r)

        # Table selector
        table_row = ft.Row(spacing=ds.space_xs, scroll=ft.ScrollMode.AUTO)
        for t in self._tables:
            table_row.controls.append(
                ft.Container(
                    ft.Text(t, size=12, weight=ft.FontWeight.BOLD,
                            color=ds.p.on_primary if self._table == t else ds.p.primary),
                    padding=ft.Padding(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs),
                    bgcolor=ds.p.primary if self._table == t else None,
                    border=ft.Border.all(1, ds.p.primary) if self._table != t else None,
                    border_radius=ds.SHAPE_FULL.radius.top_left,
                    on_click=safe_handler(lambda e, tt=t: self._set_table(tt), "Staff.commander.set_table"),
                )
            )

        view = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

        if not hasattr(self, '_cat_view') or self._cat_view is None:
            # List categories
            for (cid, cn), prods in by_cat.items():
                view.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=ds.icon_sm, color=ds.p.primary),
                            spacer(ds.space_sm),
                            ft.Text(cn, style=ds.textstyle("title_medium"), expand=True),
                            ft.Text(str(len(prods)), style=ds.textstyle("label_small"), color=ds.p.text_soft),
                        ]),
                        padding=ft.Padding(ds.space_md, ds.space_md, ds.space_md, ds.space_md),
                        border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)),
                        on_click=safe_handler(lambda e, cid=cid, cn=cn: self._show_cat(cid, cn), "Staff.commander.show_cat"),
                    )
                )
        else:
            cid, cn = self._cat_view
            prods = by_cat.get((cid, cn), [])
            view.controls.append(
                ft.Container(
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_size=18,
                                     on_click=safe_handler(lambda e: self._back_cat(), "Staff.commander.back_cat")),
                        ft.Text(cn, style=ds.textstyle("title_small"), color=ds.p.primary, expand=True),
                    ]),
                    padding=ft.Padding(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm),
                    border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)),
                )
            )
            for p in prods:
                pid = str(p["id"])
                qty = next((c["qty"] for c in self._cart if c["id"] == pid), 0)
                view.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Column([
                                ft.Text(p["nom"], style=ds.textstyle("body_medium")),
                                ft.Text(f"{float(p['prix']):,.0f} FCFA", style=ds.textstyle("label_small"), color=ds.p.text_soft),
                            ], spacing=0, expand=True),
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.REMOVE, icon_size=16,
                                             on_click=safe_handler(lambda e, pp=p: self._cart_rem(pp), "Staff.commander.cart_rem"))
                                if qty > 0 else ft.Container(width=32, height=32),
                                ft.Text(str(qty) if qty > 0 else "", size=14, weight=ft.FontWeight.BOLD, color=ds.p.primary),
                                ft.IconButton(icon=ft.Icons.ADD, icon_size=16,
                                             on_click=safe_handler(lambda e, pp=p: self._cart_add(pp), "Staff.commander.cart_add")),
                            ]),
                        ]),
                        padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
                        bgcolor=ds.p.primary_container if qty > 0 else None,
                        border=ft.Border(bottom=ft.BorderSide(1, ds.p.outline_variant)),
                    )
                )

        total = sum(c["prix"] * c["qty"] for c in self._cart)
        cart_row = ft.Container(
            ft.Row([
                ft.Text(f"{self._table} • {len(self._cart)} art. • {total:,.0f} F",
                        style=ds.textstyle("body_medium"), expand=True),
                button("Valider", variant=ButtonVariant.FILLED, icon=ft.Icons.CHECK,
                       on_click=safe_handler(lambda e: self._validate(), "Staff.commander.validate"), disabled=len(self._cart)==0),
            ]),
            padding=ft.Padding(ds.space_md, ds.space_md, ds.space_md, ds.space_md),
            bgcolor=ds.p.surface, border=ft.Border(top=ft.BorderSide(1, ds.p.outline_variant)),
        )
        return ft.Column([table_row, spacer(ds.space_sm), view, cart_row], expand=True, spacing=0)

    def _set_table(self, t):
        self._table = t; self._cat_view = None; self._show_commander()
    def _show_cat(self, cid, cn):
        self._cat_view = (cid, cn); self._show_commander()
    def _back_cat(self):
        self._cat_view = None; self._show_commander()
    def _show_commander(self):
        self._tab = 0; content = self._build_content()
        self.page.controls.clear(); self.page.add(self.tab_bar, content); self.page.update()

    def _cart_add(self, prod):
        pid = str(prod["id"])
        ex = next((c for c in self._cart if c["id"] == pid), None)
        if ex: ex["qty"] += 1
        else: self._cart.append({"id": pid, "nom": prod["nom"], "prix": float(prod["prix"]), "qty": 1})
        self._show_commander()

    def _cart_rem(self, prod):
        pid = str(prod["id"])
        ex = next((c for c in self._cart if c["id"] == pid), None)
        if ex:
            ex["qty"] -= 1
            if ex["qty"] <= 0: self._cart = [c for c in self._cart if c["id"] != pid]
        self._show_commander()

    def _validate(self):
        if not self._cart: return
        conn = _conn(); cur = conn.cursor()
        cid = str(uuid.uuid4()); total = sum(c["prix"]*c["qty"] for c in self._cart)
        eid = self.user["etablissement_id"]; uid = self.user["id"]
        cur.execute("""
            INSERT INTO commandes (id, staff_id, etablissement_id, reference_client,
                statut, type_service, total, moyen_paiement, statut_paiement, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (cid, uid, eid, self._table, "en_attente", "sur_place", total, None, "en_attente", uid))
        for c in self._cart:
            cur.execute("""
                INSERT INTO lignes_commande (id, commande_id, produit_id, quantite, prix_unitaire)
                VALUES (%s,%s,%s,%s,%s)
            """, (str(uuid.uuid4()), cid, c["id"], c["qty"], c["prix"]))
        conn.commit(); cur.close(); conn.close()
        self._cart = []; self._cat_view = None; self._show_commander()

    # ═══════════ TAB 1 — EN COURS ═══════════
    def _en_cours_view(self):
        conn = _conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.*, s.nom AS staff_nom FROM commandes c
            LEFT JOIN utilisateurs s ON c.staff_id = s.id
            WHERE c.etablissement_id=%s AND c.deleted_at IS NULL
            AND c.statut IN ('en_attente','en_preparation','pret')
            ORDER BY c.created_at DESC LIMIT 20
        """, (self.user["etablissement_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()

        status_labels = {"en_attente": "En cuisine", "en_preparation": "En preparation", "pret": "Pret a servir"}
        status_colors = {"en_attente": ds.p.tertiary, "en_preparation": ds.p.primary, "pret": ds.p.success}

        items = ft.Column(spacing=ds.space_sm, scroll=ft.ScrollMode.AUTO, expand=True)

        if not rows:
            items.controls.append(ft.Text("Aucune commande en cours", style=ds.textstyle("body_small"),
                                         color=ds.p.text_disabled, italic=True))
        for c in rows:
            lignes = self._lignes(str(c["id"]))
            items_text = ", ".join(f"{int(l['quantite'])}x {l.get('produit_nom','—')[:20]}" for l in lignes)
            st = c["statut"] or "en_attente"
            sc = status_colors.get(st, ds.p.text_soft)
            items.controls.append(
                ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Text(c.get("reference_client") or "—", style=ds.textstyle("title_medium")),
                            ft.Container(expand=True),
                            ft.Container(ft.Text(status_labels.get(st, st), size=11, color=ds.p.on_primary),
                                         padding=ft.Padding(ds.space_sm, 2, ds.space_sm, 2),
                                         bgcolor=sc, border_radius=ds.SHAPE_FULL.radius.top_left),
                        ]),
                        spacer(ds.space_xxs),
                        ft.Text(items_text, style=ds.textstyle("body_small")),
                        spacer(ds.space_xxs),
                        ft.Row([
                            ft.Text(f"{float(c['total']):,.0f} FCFA", style=ds.textstyle("label_small"), color=ds.p.text_soft),
                            ft.Container(expand=True),
                            button("Servi ✓", variant=ButtonVariant.FILLED, on_click=safe_handler(lambda e, cid=str(c["id"]): self._servir(cid), "Staff.en_cours.servir"))
                            if st == "pret" else None,
                            button("Ajouter", variant=ButtonVariant.OUTLINED, on_click=safe_handler(lambda e, cid=str(c["id"]): self._add_to(cid), "Staff.en_cours.add_to"))
                            if st != "pret" else None,
                        ]),
                    ]),
                    padding=ft.Padding(ds.space_md, ds.space_md, ds.space_md, ds.space_md),
                    bgcolor=ds.p.surface, border_radius=ds.SHAPE_MD.radius.top_left,
                    border=ft.Border(left=ft.BorderSide(3, sc)),
                )
            )

        return ft.Column([
            ft.Container(
                ft.Row([headline("Commandes en cours", size="small"),
                        ft.IconButton(icon=ft.Icons.REFRESH, icon_size=18, on_click=safe_handler(lambda e: self._show_en_cours(), "Staff.en_cours.refresh"))]),
                padding=ft.Padding(ds.space_md, ds.space_md, ds.space_md, 0),
            ),
            items,
        ], expand=True)

    def _servir(self, cid):
        conn = _conn(); cur = conn.cursor()
        cur.execute("UPDATE commandes SET statut='livre', updated_at=NOW() WHERE id=%s", (cid,))
        conn.commit(); cur.close(); conn.close()
        self._show_en_cours()

    def _add_to(self, cid):
        # For now: simple notification that this feature is coming
        self._show_en_cours()

    def _show_en_cours(self):
        self._tab = 1; self._show_main()

    def _lignes(self, cid):
        conn = _conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT lc.*, p.nom AS produit_nom FROM lignes_commande lc
            JOIN produits p ON lc.produit_id = p.id
            WHERE lc.commande_id=%s AND lc.deleted_at IS NULL
        """, (cid,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return rows

    # ═══════════ TAB 2 — ENCAISSER ═══════════
    def _encaisser_view(self):
        conn = _conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.* FROM commandes c
            WHERE c.etablissement_id=%s AND c.deleted_at IS NULL
            AND c.statut_paiement='en_attente' AND c.statut IN ('pret','livre')
            ORDER BY c.created_at ASC
        """, (self.user["etablissement_id"],))
        to_pay = [dict(r) for r in cur.fetchall()]

        # CA du serveur
        cur.execute("""
            SELECT moyen_paiement, SUM(total) as total, COUNT(*) as nb
            FROM commandes
            WHERE etablissement_id=%s AND staff_id=%s AND statut_paiement='paye'
            AND created_at>=CURRENT_DATE AND deleted_at IS NULL
            GROUP BY moyen_paiement
        """, (self.user["etablissement_id"], self.user["id"]))
        ca = {r["moyen_paiement"]: float(r["total"]) for r in cur.fetchall()}
        cur.close(); conn.close()

        total_ca = sum(ca.values())
        paiement_labels = {"cash": "Especes", "tmoney": "TMoney", "flooz": "Flooz"}

        items = ft.Column(spacing=ds.space_sm, scroll=ft.ScrollMode.AUTO, expand=True)

        # CA section
        items.controls.append(
            ft.Container(
                ft.Column([
                    headline("Mon CA aujourd'hui", size="small"),
                    spacer(ds.space_sm),
                    ft.Row([kpi(f"{ca.get(k, 0):,.0f} F", paiement_labels.get(k, k)) for k in ca if ca[k] > 0] or
                           [ft.Text("Aucun encaissement", size=12, color=ds.p.text_disabled)]),
                    spacer(ds.space_xxs),
                    ft.Text(f"Total : {total_ca:,.0f} FCFA", style=ds.textstyle("title_medium"), color=ds.p.primary),
                ]),
                padding=ft.Padding(ds.space_md, ds.space_md, ds.space_md, ds.space_md),
                bgcolor=ds.p.primary_container, border_radius=ds.SHAPE_MD.radius.top_left,
            )
        )
        items.controls.append(spacer(ds.space_md))

        # Unpaid orders
        if to_pay:
            items.controls.append(headline("A encaisser", size="small"))
            for c in to_pay:
                table_ref = c.get("reference_client") or "—"
                items.controls.append(
                    ft.Container(
                        ft.Row([
                            ft.Column([
                                ft.Text(f"{table_ref} • {float(c['total']):,.0f} FCFA",
                                        style=ds.textstyle("body_medium")),
                                ft.Text(f"Statut : {c['statut']}", size=11, color=ds.p.text_soft),
                            ], spacing=0, expand=True),
                            button("Payer", variant=ButtonVariant.FILLED, icon=ft.Icons.PAYMENTS,
                                   on_click=safe_handler(lambda e, cid=str(c["id"]): self._payer(cid), "Staff.encaisser.payer")),
                        ]),
                        padding=ft.Padding(ds.space_md, ds.space_md, ds.space_md, ds.space_md),
                        bgcolor=ds.p.surface, border_radius=ds.SHAPE_MD.radius.top_left,
                        border=ft.Border(left=ft.BorderSide(3, ds.p.error)),
                    )
                )
        else:
            items.controls.append(ft.Text("Rien a encaisser", size=12, color=ds.p.text_disabled, italic=True))

        return ft.Column([items], expand=True)

    def _payer(self, cid):
        conn = _conn(); cur = conn.cursor()
        cur.execute("""
            UPDATE commandes SET statut_paiement='paye', moyen_paiement='cash',
                statut='livre', updated_by=%s, updated_at=NOW()
            WHERE id=%s
        """, (self.user["id"], cid))
        conn.commit(); cur.close(); conn.close()
        self._tab = 2; self._show_main()

    # ═══════════ TAB 3 — KDS (Cuisine) ═══════════
    def _kds_view(self):
        conn = _conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.* FROM commandes c
            WHERE c.etablissement_id=%s AND c.deleted_at IS NULL
            AND c.statut IN ('en_attente','en_preparation','pret')
            ORDER BY c.created_at ASC LIMIT 30
        """, (self.user["etablissement_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()

        now = datetime.now(timezone.utc)
        cols_data = {"en_attente":[],"en_preparation":[],"pret":[]}
        for r in rows:
            st = r["statut"] or "en_attente"
            if st in cols_data: cols_data[st].append(r)

        labels = {"en_attente":"En attente","en_preparation":"En preparation","pret":"Pret"}
        colors = {"en_attente":ds.p.tertiary,"en_preparation":ds.p.primary,"pret":ds.p.success}
        next_st = {"en_attente":"en_preparation","en_preparation":"pret"}

        kanban = ft.Row(expand=True, spacing=ds.space_sm, scroll=ft.ScrollMode.AUTO)
        for st in ("en_attente","en_preparation","pret"):
            cmds = cols_data[st]
            col = ft.Column(spacing=ds.space_sm)
            col.controls.append(
                ft.Container(
                    ft.Row([
                        ft.Text(labels[st], style=ds.textstyle("title_small"), color=colors[st]),
                        ft.Container(ft.Text(str(len(cmds)), size=12, color=ds.p.on_primary),
                                    padding=ft.Padding(ds.space_sm,2,ds.space_sm,2),
                                    bgcolor=colors[st], border_radius=ds.SHAPE_FULL.radius.top_left),
                    ]),
                    padding=ft.Padding(ds.space_sm,ds.space_sm,ds.space_sm,ds.space_sm),
                    border=ft.Border(bottom=ft.BorderSide(2, colors[st])),
                )
            )
            for c in cmds:
                lignes = self._lignes(str(c["id"]))
                txt = "  ".join(f"{int(l['quantite'])}x {l.get('produit_nom','—')[:12]}" for l in lignes)
                ct = c.get("created_at")
                if ct:
                    delta = now - (ct.replace(tzinfo=timezone.utc) if ct.tzinfo is None else ct)
                    ts = f"{max(0,int(delta.total_seconds()/60))}m"
                else: ts = ""
                ns = next_st.get(st)
                col.controls.append(
                    ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c.get("reference_client") or "—", size=11, weight=ft.FontWeight.BOLD),
                                ft.Text(ts, size=9, color=ds.p.text_disabled), ft.Container(expand=True),
                                ft.IconButton(icon=ft.Icons.ARROW_FORWARD, icon_size=16,
                                             icon_color=colors.get(ns),
                                             on_click=safe_handler(lambda e, cid=str(c["id"]), ns2=ns: (
                                                 self._ch_kds(cid, ns2), self._show_kds()
                                             ), "Staff.kds.move_card")) if ns else None,
                            ]),
                            ft.Text(txt, style=ds.textstyle("body_small")),
                        ]),
                        padding=ds.space_sm, bgcolor=ds.p.surface,
                        border_radius=ds.SHAPE_SM.radius.top_left,
                        border=ft.Border(left=ft.BorderSide(3, colors[st])),
                    )
                )
            kanban.controls.append(
                ft.Container(col, width=190, bgcolor=ds.p.surface_variant,
                            border_radius=ds.SHAPE_MD.radius.top_left)
            )
        return ft.Column([
            ft.Row([headline("Cuisine - KDS", size="small"),
                    ft.IconButton(icon=ft.Icons.REFRESH, icon_size=18, on_click=safe_handler(lambda e: self._show_kds(), "Staff.kds.refresh"))]),
            kanban,
        ], expand=True)

    def _ch_kds(self, cid, ns):
        if not ns: return
        conn = _conn(); cur = conn.cursor()
        cur.execute("UPDATE commandes SET statut=%s WHERE id=%s", (ns, cid))
        conn.commit(); cur.close(); conn.close()

    def _show_kds(self):
        self._tab = 3; self._show_main()


def kpi(val, lbl):
    return ft.Container(
        ft.Column([
            ft.Text(val, style=ds.textstyle("title_small")),
            ft.Text(lbl, style=ds.textstyle("label_small"), color=ds.p.text_soft),
        ], spacing=0),
        padding=ft.Padding(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm),
        bgcolor=ds.p.background, border_radius=ds.SHAPE_SM.radius.top_left,
        expand=True, alignment=ft.alignment.Alignment(0, 0),
    )


def main(page: ft.Page):
    set_debug(True)
    page.title = "ArtizBoard — Staff"
    page.window.width = 420; page.window.height = 800; page.padding = 0
    # Footer licence
    page.theme_mode = ft.ThemeMode.LIGHT
    StaffApp(page).run()

if __name__ == "__main__":
    ft.app(target=main)
