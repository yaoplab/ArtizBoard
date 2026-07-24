---
tags:
  - skill
  - crud-m3
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: **Jamais** de `DELETE CASCADE` — toujours `UPDATE ... SET deleted_at = NOW()` (soft delete)
- **C2**: **UUID v4** généré côté application avant INSERT (`uuid.uuid4()`), pas `uuid_generate_v4()`
- **C3**: **Optimistic locking** : chaque UPDATE vérifie `WHERE version = X` et incrémente `version = X + 1`
- **C4**: Si `cur.rowcount == 0` après UPDATE → `raise ValueError` (le record a été modifié par un autre)
- **C5**: **Audit trail** systématique : `created_by`, `updated_by` remplis avec l'UUID de l'utilisateur
- **C6**: Le `sync_status` est mis à `'local'` à la création, marqué `'pending'` puis `'synced'` par le sync
- **C7**: Les requêtes incluent toujours `WHERE deleted_at IS NULL` sauf pour l'admin qui peut voir les soft-deleted

## [[2a-insert|Sous-système A: INSERT]]

## [[2b-update|Sous-système B: UPDATE]]

## [[2c-delete-(soft)|Sous-système C: DELETE (soft)]]

## [[2d-dialogs|Sous-système D: Dialogs]]

