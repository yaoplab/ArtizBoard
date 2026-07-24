---
tags:
  - skill
  - crud-m3
  - contrainte
  - sous-systeme
  - priorite-2
---

# Sous-système C: DELETE (soft)

- **C1**: `soft_delete(table, id, deleted_by)` → `UPDATE table SET deleted_at=NOW(), updated_by=%s WHERE id=%s AND deleted_at IS NULL`
- **C2**: Les enregistrements soft-deleted sont exclus de toutes les queries par `WHERE deleted_at IS NULL`
- **C3**: Seul l'admin peut voir/restaurer les soft-deleted (via une vue dédiée)
