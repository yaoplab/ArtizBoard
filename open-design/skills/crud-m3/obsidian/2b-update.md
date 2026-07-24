---
tags:
  - skill
  - crud-m3
  - contrainte
  - sous-systeme
  - priorite-1
---

# Sous-système B: UPDATE

- **B1**: L'UPDATE reçoit `version` du frontend et vérifie `WHERE id=%s AND version=%s AND deleted_at IS NULL`
- **B2**: L'UPDATE incrémente `version = version + 1` et met à jour `updated_by`, `updated_at`
- **B3**: Si `rowcount == 0` → rollback immédiat + `raise ValueError("Modifie par un autre utilisateur")`
