# Skill: Catalogue 3 Panneaux (v2 — 10/10)

## When to apply
- Building any product/entity catalog
- Multi-panel master-detail layouts
- CRUD interfaces with list + detail

## Structure
```
Left(300px)      |  Middle(expand=1)    |  Right(expand=2)
[Categories]      |  [Products filtered] |  [Detail + Photo + Price + Stock]
  + Add button    |    + Add button      |    Edit / Delete buttons
```

## Panels — code patterns

### Left — Categories
```python
cat_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
for c in categories:
    sel = c["id"] == self._catsel
    cat_list.controls.append(ft.Container(
        ft.Row([ft.Icon(CIRCLE if sel else CIRCLE_OUTLINED, size=10,
                color=ds.p.primary if sel else ds.p.text_disabled),
                spacer(ds.space_xs),
                ft.Text(c["nom"], size=14, weight=BOLD if sel else NORMAL,
                        color=ds.p.primary if sel else ds.p.text_strong)]),
        padding=ft.Padding(ds.space_sm,ds.space_xs,ds.space_sm,ds.space_xs),
        bgcolor=ds.p.primary_container if sel else None,
        border_radius=ds.SHAPE_XS.radius.top_left,
        on_click=lambda e, cc=c: select_cat(cc)))
```

### Middle — Products
```python
for p in products:
    stock_color = ds.p.error if p["stock"] <= p["stock_alerte"] else ds.p.text_soft
    prod_list.controls.append(ft.Container(
        ft.Row([
            ft.Container(ft.Text(str(p["stock"]),size=11,color=stock_color),
                        width=28,height=28,bgcolor=ds.p.surface_variant,
                        border_radius=ds.SHAPE_XS.radius.top_left),
            spacer(ds.space_sm),
            ft.Column([ft.Text(p["nom"],size=14),
                       ft.Text(f"{float(p['prix']):,.0f} FCFA",size=11,color=ds.p.text_soft)],
                      spacing=0,expand=True)]),
        bgcolor=ds.p.primary_container if p["id"]==self._prodsel else None,
        padding=ft.Padding(ds.space_sm,ds.space_xs,ds.space_sm,ds.space_xs),
        on_click=lambda e, pp=p: select_prod(pp)))
```

### Right — Detail
```python
# Photo
if p.get("photo_url"):
    ft.Image(src=p["photo_url"], fit="cover", height=200,
             border_radius=ds.SHAPE_MD.radius.top_left)
else:
    ft.Container(ft.Icon(IMAGE,64,ds.p.text_disabled),height=200)

# KPI row
ft.Row([
    info_box("PRIX", f"{float(p['prix']):,.0f} FCFA", ds.p.primary),
    spacer(ds.space_lg),
    info_box("STOCK", str(p["stock"]), sc),
    spacer(ds.space_lg),
    info_box("ALERTE", str(p.get("stock_alerte",5)), ds.p.text_soft),
])
# Description
ft.Markdown(p.get("description",""), extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED)
# Actions
ft.Row([ft.FilledTonalButton(content=ft.Text("Modifier"), icon=ft.Icons.EDIT, on_click=edit),
        ft.TextButton("Supprimer", icon=ft.Icons.DELETE, on_click=confirm_delete)])
```

## Dialogs

### Add/Edit Product
```python
dlg = ft.AlertDialog(
    title=ft.Text("Ajouter" if new else "Modifier"),
    content=ft.Column([...fields...], height=400, scroll=ft.ScrollMode.AUTO),
    actions=[ft.TextButton("Annuler", close), ft.FilledButton(content=ft.Text("Enregistrer"), icon=ft.Icons.SAVE, on_click=save)])
page.show_dialog(dlg)
```

### Add Category
```python
dlg = ft.AlertDialog(
    title=ft.Text("Nouvelle categorie"),
    content=ft.Column([ft.TextField(label="Nom",width=300), err], width=320),
    actions=[ft.TextButton("Annuler", close), ft.FilledButton(content=ft.Text("Creer"), icon=ft.Icons.ADD, on_click=save)])
```

### Confirm Delete
```python
dlg = ft.AlertDialog(
    title=ft.Text("Confirmer"),
    content=ft.Text(f"Supprimer '{nom}' ?"),
    actions=[ft.TextButton("Annuler", close), ft.FilledButton(content=ft.Text("Supprimer"), icon=ft.Icons.DELETE, on_click=do_delete)])
```

## Refresh pattern — CRITICAL
```python
# Initial population: populate controls inline (NO .update() call)
for c in categories: cat_list.controls.append(...)

# Refresh from event handler: clear + rebuild + update
def refresh():
    data = fetch_from_db()
    list_control.controls.clear()
    for item in data: list_control.controls.append(build_item(item))
    try: list_control.update()
    except RuntimeError: pass  # Not mounted yet
```

## CRUD rules
```python
INSERT INTO produits (id, ..., created_by, updated_by) VALUES (uuid4(), ..., uid, uid)
UPDATE produits SET ..., version=version+1 WHERE id=%s AND version=%s AND deleted_at IS NULL
UPDATE produits SET deleted_at=NOW() WHERE id=%s  # soft delete
```

## Empty states
```
No categories → ft.Text("Aucune categorie. Cliquez + pour en creer.", italic=True)
No products → ft.Text("Aucun produit dans cette categorie.", italic=True)
No detail → ft.Icon(IMAGE,64,disabled) + "Selectionnez un produit"
```

## Emplacement
`apps/admin/__main__.py` — `_catalogue_content()`, `_edit_produit()`, `_confirm_delete()`
