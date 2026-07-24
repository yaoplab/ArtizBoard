---
tags:
  - skill
  - crud-m3
  - contrainte
  - sous-systeme
  - priorite-3
---

# Sous-système D: Dialogs

- **D1**: Le dialog de création/modification est un `ft.AlertDialog` avec `title`, `content` (champs), `actions` (boutons)
- **D2**: Le dialog de suppression demande confirmation : "Supprimer X ?" avec boutons "Annuler" et "Supprimer"
- **D3**: Le `shape` du dialog est `ft.RoundedRectangleBorder(ds.SHAPE_MD.radius.top_left)`
- **D4**: La fermeture de dialog se fait via `dlg.open = False; self.page.update()`
