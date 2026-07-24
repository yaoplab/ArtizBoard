"""Quick fix: override _edit_produit to use local scope like add_cat_dialog"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Read the file
path = r"C:\projet\apps\admin\__main__.py"
with open(path, encoding="utf-8") as f:
    content = f.read()

# Replace _edit_produit (from line 1000 def to line 1098 _ = categories)
old_method_start = content.find("    def _edit_produit(self, produit_id: str = None, cat_id: str = None):")
old_method_end = content.find("    def _catalogue_content(self):")

new_method = '''    def _edit_produit(self, produit_id=None, cat_id=None):
        """Ouvre le dialogue produit."""
        categories = self._fetch_categories()
        produit = None
        if produit_id:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM produits WHERE id=%s AND deleted_at IS NULL", (produit_id,))
            produit = cur.fetchone()
            cur.close()

        w = 360
        nom = textfield(label="Nom", value=produit["nom"] if produit else "", width=w)
        cat_dd = ft.Dropdown(
            label="Categorie",
            options=[ft.dropdown.Option(str(c["id"]), c["nom"]) for c in categories],
            value=str(produit["categorie_id"]) if produit else (cat_id or None),
            width=w, border_radius=ds.SHAPE_XS.radius.top_left,
        )
        prix = textfield(label="Prix (FCFA)", value=str(produit["prix"]) if produit else "", width=w)
        desc = textfield(label="Description", value=produit["description"] if produit else "", width=w, multiline=True, max_lines=3)
        stock_tf = textfield(label="Stock", value=str(produit["stock"]) if produit else "0", width=w)
        alerte_tf = textfield(label="Seuil alerte", value=str(produit.get("stock_alerte", 5)) if produit else "5", width=w)
        tva_tf = textfield(label="TVA (%)", value=str(produit.get("taux_tva", 0)) if produit else "0", width=w)
        disponible = ft.Checkbox(label="Disponible a la commande", value=produit["permets_commande"] if produit else True)
        photo_url_tf = textfield(label="Photo (URL)", value=produit.get("photo_url", "") if produit else "", width=w)
        err = ft.Text("", color=ds.p.error, size=ds.typo.label_small.size)

        def do_save(e):
            try:
                p = float(prix.value or 0)
                s = int(stock_tf.value or 0)
            except ValueError:
                err.value = "Prix et stock doivent etre numeriques"; err.update(); return
            if not cat_dd.value:
                err.value = "Categorie requise"; err.update(); return
            data = {
                "id": produit_id, "nom": nom.value.strip(), "categorie_id": cat_dd.value,
                "description": desc.value.strip(), "prix": p, "taux_tva": float(tva_tf.value or 0),
                "stock": s, "stock_alerte": int(alerte_tf.value or 5), "permets_commande": disponible.value,
                "photo_url": photo_url_tf.value.strip(),
            }
            if produit: data["version"] = produit["version"]
            try:
                self._save_produit(data)
                dlg.open = False; self.page.update()
                self._navigate("catalogue")
            except ValueError as ex:
                err.value = str(ex); err.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Modifier" if produit else "Ajouter un produit", style=ds.textstyle("title_medium")),
            content=ft.Column([nom, spacer(ds.space_sm), cat_dd, spacer(ds.space_sm),
                prix, spacer(ds.space_sm), tva_tf, spacer(ds.space_sm),
                stock_tf, spacer(ds.space_sm), alerte_tf, spacer(ds.space_sm),
                desc, spacer(ds.space_sm), photo_url_tf, spacer(ds.space_sm),
                disponible, spacer(ds.space_sm), err],
                scroll=ft.ScrollMode.AUTO, spacing=0),
            actions=[
                button("Annuler", variant=ButtonVariant.TEXT, on_click=lambda e: (setattr(dlg, 'open', False), self.page.update())),
                button("Enregistrer", variant=ButtonVariant.FILLED, icon=ft.Icons.SAVE, on_click=do_save),
            ],
            shape=ft.RoundedRectangleBorder(ds.SHAPE_MD.radius.top_left),
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

'''

content = content[:old_method_start] + new_method + content[old_method_end:]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("_edit_produit remplace. Verification compilation...")
import py_compile
py_compile.compile(path, doraise=True)
print("OK")
