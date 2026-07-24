---
tags:
  - skill
  - kds-kanban
  - contrainte
  - sous-systeme
  - priorite-2
---

# Sous-système C: Fetch des lignes

- **C1**: `_lignes(cmd_id)` → jointure `lignes_commande` + `produits` pour obtenir le nom des plats
- **C2**: Retourne une liste de dicts : `[{"quantite": 2, "produit_nom": "Riz au Gras", ...}]`
- **C3**: Les lignes soft-deletées sont exclues (`deleted_at IS NULL`)
