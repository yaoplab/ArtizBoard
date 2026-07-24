# Skill: CRUD M3

## 0. Contexte

**Projet** : ArtizBoard
**Module** : Patterns DB — toutes les apps
**Utilisateurs** : Admin, Staff
**Dépendances** : PostgreSQL, soft delete, UUID
**Prérequis** : Connexion DB via PgBouncer


## 1. Fonction Principale

### Type : Système Fermé

```
ENTRÉE                         →  TRAITEMENT                             →  SORTIE
Nom de table SQL                  UUID v4 génération + audit              ├─ Enregistrement créé/modifié/supprimé
Données dict (colonnes/valeurs)   WHERE version=X (optimistic lock)       ├─ sync_status mis à jour
Utilisateur connecté (UUID)       UPDATE/INSERT/DELETE avec audit trail   └─ Exception si conflit
```

## 2. Contraintes Fonctionnelles

### Tableau global

| # | Contrainte |
|---|---|
| C1 | **Jamais** de `DELETE CASCADE` — toujours `UPDATE ... SET deleted_at = NOW()` (soft delete) |
| C2 | **UUID v4** généré côté application avant INSERT (`uuid.uuid4()`), pas `uuid_generate_v4()` |
| C3 | **Optimistic locking** : chaque UPDATE vérifie `WHERE version = X` et incrémente `version = X + 1` |
| C4 | Si `cur.rowcount == 0` après UPDATE → `raise ValueError` (le record a été modifié par un autre) |
| C5 | **Audit trail** systématique : `created_by`, `updated_by` remplis avec l'UUID de l'utilisateur |
| C6 | Le `sync_status` est mis à `'local'` à la création, marqué `'pending'` puis `'synced'` par le sync |
| C7 | Les requêtes incluent toujours `WHERE deleted_at IS NULL` sauf pour l'admin qui peut voir les soft-deleted |

### Sous-système A — INSERT

| # | Contrainte |
|---|---|
| A1 | `INSERT` inclut `id`, `created_by`, `updated_by`, `created_at`, `updated_at` |
| A2 | `sync_status` initialisé à `'local'` |
| A3 | `version` initialisé à 1 |

### Sous-système B — UPDATE

| # | Contrainte |
|---|---|
| B1 | L'UPDATE reçoit `version` du frontend et vérifie `WHERE id=%s AND version=%s AND deleted_at IS NULL` |
| B2 | L'UPDATE incrémente `version = version + 1` et met à jour `updated_by`, `updated_at` |
| B3 | Si `rowcount == 0` → rollback immédiat + `raise ValueError("Modifie par un autre utilisateur")` |

### Sous-système C — DELETE (soft)

| # | Contrainte |
|---|---|
| C1 | `soft_delete(table, id, deleted_by)` → `UPDATE table SET deleted_at=NOW(), updated_by=%s WHERE id=%s AND deleted_at IS NULL` |
| C2 | Les enregistrements soft-deleted sont exclus de toutes les queries par `WHERE deleted_at IS NULL` |
| C3 | Seul l'admin peut voir/restaurer les soft-deleted (via une vue dédiée) |

### Sous-système D — Dialogs

| # | Contrainte |
|---|---|
| D1 | Le dialog de création/modification est un `ft.AlertDialog` avec `title`, `content` (champs), `actions` (boutons) |
| D2 | Le dialog de suppression demande confirmation : "Supprimer X ?" avec boutons "Annuler" et "Supprimer" |
| D3 | Le `shape` du dialog est `ft.RoundedRectangleBorder(ds.SHAPE_MD.radius.top_left)` |
| D4 | La fermeture de dialog se fait via `dlg.open = False; self.page.update()` |

## 3. Code complet

### Soft Delete

```python
def soft_delete(table: str, record_id: str, deleted_by: str, conn) -> None:
    """Soft delete a record. Never CASCADE."""
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE {table} SET deleted_at = NOW(), updated_by = %s
        WHERE id = %s AND deleted_at IS NULL
    """, (deleted_by, record_id))
    if cur.rowcount == 0:
        raise ValueError(f"Enregistrement {record_id} introuvable ou deja supprime")
    conn.commit()
    cur.close()
```

### INSERT with audit

```python
def insert_record(table: str, data: dict, eid: str, uid: str, conn) -> str:
    """Insert with UUID + audit trail."""
    import uuid
    pid = str(uuid.uuid4())
    cur = conn.cursor()
    # Construire dynamiquement les colonnes et valeurs
    cols = ["id", "etablissement_id", "created_by", "updated_by"]
    vals = [pid, eid, uid, uid]
    for k, v in data.items():
        cols.append(k)
        vals.append(v)
    placeholders = ", ".join(["%s"] * len(vals))
    cur.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})", vals)
    conn.commit(); cur.close()
    return pid
```

### UPDATE with optimistic lock

```python
def update_record(table: str, record_id: str, data: dict, version: int, uid: str, conn) -> None:
    """Update with optimistic locking. Raises ValueError on conflict."""
    cur = conn.cursor()
    sets = ", ".join([f"{k}=%s" for k in data.keys()])
    vals = list(data.values()) + [uid, record_id, version]
    cur.execute(f"""
        UPDATE {table} SET {sets}, updated_by = %s, updated_at = NOW(), version = version + 1
        WHERE id = %s AND version = %s AND deleted_at IS NULL
    """, vals)
    if cur.rowcount == 0:
        conn.rollback()
        raise ValueError(f"Conflit: {table}/{record_id} modifie par un autre utilisateur")
    conn.commit()
    cur.close()
```

### Fetch pattern

```python
def fetch_all(table: str, etablissement_id: str, conn) -> list[dict]:
    """Fetch all non-deleted records for an establishment."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT * FROM {table} WHERE etablissement_id = %s AND deleted_at IS NULL ORDER BY created_at DESC",
                (etablissement_id,))
    rows = [dict(r) for r in cur.fetchall()]; cur.close()
    return rows
```

### Dialog — Créer/Modifier

```python
def edit_dialog(page: ft.Page, record: dict | None, on_save: callable, fields: list):
    """Generic edit dialog. record=None for new."""
    is_new = record is None
    dlg = ft.AlertDialog(
        title=ft.Text("Ajouter" if is_new else "Modifier", style=ds.textstyle("title_medium")),
        content=ft.Column(fields, width=400, scroll=ft.ScrollMode.AUTO),
        actions=[
            bt("Annuler", ButtonVariant.TEXT, on_click=lambda e: set_close(dlg, page)),
            bt("Enregistrer", ButtonVariant.FILLED, icon=_.SAVE, on_click=lambda e: on_save()),
        ],
        shape=ft.RoundedRectangleBorder(ds.SHAPE_MD.radius.top_left),
    )
    page.dialog = dlg; dlg.open = True; page.update()

def set_close(dlg, page):
    dlg.open = False; page.update()
```

## 4. Deux exemples

### Exemple 1 — Créer un produit (cas simple)

```python
def save_produit(data, user, conn):
    if data.get("id"):
        update_record("produits", data["id"], data, data["version"], user["id"], conn)
    else:
        pid = insert_record("produits", data, user["etablissement_id"], user["id"], conn)
    # Sync status sera géré par sync_service
```

### Exemple 2 — Conflit de version (edge case)

```python
try:
    update_record("produits", "abc-123", {"prix": 5000}, version=3, uid="admin-1", conn=conn)
except ValueError as e:
    # Afficher à l'utilisateur : "Ce produit a été modifié par quelqu'un d'autre. Rechargez."
    page.snack_bar = ft.SnackBar(ft.Text(str(e)), open=True)
    page.update()
    # Recharger les données fraîches
    produit = fetch_all("produits", eid, conn)
```

## 5. Step by Step — Implementation

| Ordre | Action | Fichier | Resultat |
|---|---|---|---|
| 1 | Implémenter soft_delete (table, id, uid) | Module DB | DELETE logique |
| 2 | Implémenter insert_record avec UUID + audit | Module DB | INSERT avec traçabilité |
| 3 | Implémenter update_record avec optimistic lock | Module DB | UPDATE avec détection conflit |
| 4 | Implémenter fetch_all avec deleted_at IS NULL | Module DB | Lecture filtrée |
| 5 | Créer dialogs M3 (créer, modifier, confirmer) | UI | Interfaces standardisées |
| 6 | Tester : conflit version → ValueError | pytest | Exception levée correctement |

## Checklist

- [ ] Soft delete partout, jamais CASCADE
- [ ] UUID v4 côté app
- [ ] Optimistic locking sur chaque UPDATE
- [ ] Audit trail (created_by, updated_by)
- [ ] Dialogs M3 avec shape MD, actions cohérentes
- [ ] Conflit détecté → message utilisateur + relancer

## Emplacement
- Models : `apps/admin/__main__.py` (méthodes `_save_*`, `_delete_*`, `_fetch_*`)
- Dialogs : même fichier, méthodes `_edit_*_dialog`, `_confirm_delete`
