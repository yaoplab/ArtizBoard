---
tags:
  - skill
  - kds-kanban
  - contrainte
  - sous-systeme
  - priorite-1
---

# Sous-système B: Avancement de commande

- **B1**: `_ch_kds(cmd_id, new_statut)` → `UPDATE commandes SET statut=%s WHERE id=%s`
- **B2**: La flèche n'apparaît que s'il existe un statut suivant (pas sur "Prêt")
- **B3**: Après avancement, le kanban est rafraîchi immédiatement
