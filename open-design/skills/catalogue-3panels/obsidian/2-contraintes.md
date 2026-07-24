---
tags:
  - skill
  - catalogue-3panels
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: Le layout est un `ft.Row` avec 3 enfants : gauche(200px) + centre(expand=1) + droite(expand=2)
- **C2**: La sélection d'une catégorie filtre les produits affichés au centre
- **C3**: La sélection d'un produit affiche son détail à droite
- **C4**: Les rafraîchissements utilisent le pattern safe : `try: control.update() except RuntimeError: pass`
- **C5**: Le CRUD suit les règles du skill `crud-m3` (soft delete, optimistic lock, UUID)
- **C6**: Les données sont fetchées depuis PgBouncer (`_get_conn()` → `RealDictCursor`)

## [[2a-panneau-gauche-(catégories)|Sous-système A: Panneau gauche (catégories)]]

## [[2b-panneau-central-(produits)|Sous-système B: Panneau central (produits)]]

## [[2c-panneau-droit-(détail)|Sous-système C: Panneau droit (détail)]]

