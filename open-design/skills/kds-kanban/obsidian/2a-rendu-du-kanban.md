---
tags:
  - skill
  - kds-kanban
  - contrainte
  - sous-systeme
  - priorite-3
---

# Sous-système A: Rendu du kanban

- **A1**: Les colonnes sont dans un `ft.Row` horizontal, chaque colonne dans `ft.Container` de largeur 190px
- **A2**: Chaque carte est un `ft.Container` avec fond `ds.p.surface`, radius `ds.SHAPE_SM`, bordure gauche colorée 3px
- **A3**: Le temps est calculé : `(now - created_at).total_seconds() / 60` arrondi en minutes
- **A4**: Les plats sont listés avec l'API `_lignes()` : `quantite x nom_produit (tronqué à 12 car.)`
