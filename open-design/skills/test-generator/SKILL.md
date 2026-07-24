# Skill: Générateur de Tests

## 0. Contexte

**Projet** : ArtizBoard
**Module** : `tests/` — batterie de tests complète
**Utilisateurs** : Développeurs, agents IA, CI/CD
**Dépendances** : `conftest.py` (fixtures DB), `pytest`
**Prérequis** : PostgreSQL local accessible, données seed exécutées

## 1. Fonction Principale

### Type : Système Fermé

```
ENTRÉE                              →  TRAITEMENT                           →  SORTIE
Module/cible (admin|staff|client)      Créer classes TestXxx                   ├─ Fichier tests/test_xxx.py
Fixtures DB (conftest.py)              Méthodes test_* par fonctionnalité      ├─ pytest reports (CR)
                                       Assertions + edge cases                 └─ 100% pass ou skip motivé
```

## 2. Contraintes Fonctionnelles

### Tableau global

| # | Contrainte |
|---|---|
| C1 | Chaque module a son fichier de test : `test_admin.py`, `test_staff.py`, `test_client.py`, `test_stock.py` |
| C2 | Chaque test est une méthode `test_xxx` dans une classe `TestXxx` |
| C3 | Les fixtures sont réutilisées depuis `conftest.py` : `db_conn`, `cur`, `admin_id`, `etab_id`, `auth` |
| C4 | Les tests de DB utilisent des transactions qui font rollback après chaque test |
| C5 | Les tests UI (Flet) sont `skip` avec motif `"UI test requires display"` |
| C6 | Chaque fonctionnalité critique a un test : création, lecture, modification, suppression (CRUD) |
| C7 | Chaque test vérifie : succès nominal + au moins 1 cas d'erreur |
| C8 | Les tests sont **indépendants** — l'ordre d'exécution n'importe pas |
| C9 | Le ratio minimum est de **2 tests par endpoint/méthode publique** |

### Sous-système A — Test Admin

| # | Contrainte |
|---|---|
| A1 | Tester le catalogue : `_fetch_produits`, `_save_produit` (créer + modifier), `_delete_produit` (soft) |
| A2 | Tester les catégories : `_fetch_categories`, `_save_categorie` |
| A3 | Tester les utilisateurs : `_fetch_users`, `_save_user` (créer + modifier), activation codes |
| A4 | Tester les pages_etablissement : `_fetch_pages`, `_save_page`, `_delete_page` |
| A5 | Tester theme_config : `_fetch_theme_config`, `_save_theme_config`, `_fetch_theme_presets` |
| A6 | Tester les commandes : `_fetch_commandes`, `_change_statut`, `_fetch_lignes` |
| A7 | Tester l'upload d'image : vérifier que l'URL est stockée |

### Sous-système B — Test Staff

| # | Contrainte |
|---|---|
| B1 | Tester la prise de commande : `_validate()` crée commandes + lignes_commande |
| B2 | Tester le panier : ajouter, retirer, vider |
| B3 | Tester le KDS : `_ch_kds` change le statut |
| B4 | Tester l'encaissement : `_payer` met à jour `statut_paiement = 'paye'` |
| B5 | Tester les tables : `_set_table`, `_tables` |
| B6 | Tester le CA serveur : requête agrégée par moyen de paiement |

### Sous-système C — Test Client

| # | Contrainte |
|---|---|
| C1 | Tester le checkout : `_checkout()` crée commande + lignes |
| C2 | Tester le panier client : `addToCart`, `removeFromCart`, `getCartTotal` |
| C3 | Tester la navigation : chaque onglet renvoie le bon contenu |
| C4 | Tester la détection QR table : `?table=T12` → `reference_client = T12` |

### Sous-système D — Test Stock

| # | Contrainte |
|---|---|
| D1 | Vérifier que le stock est décrémenté après validation de commande |
| D2 | Vérifier l'alerte rupture : `stock <= stock_alerte` |
| D3 | Vérifier que `permets_commande = FALSE` bloque l'affichage |
| D4 | Tester les mouvements_stock : création automatique à la vente |

### Sous-système E — Test Invoice (fix skip)

| # | Contrainte |
|---|---|
| E1 | `test_generate_invoice` doit passer avec la vraie DB et un mock PDF |
| E2 | `test_invoice_number_format` vérifie `FAC-YYYYMMDD-XXXXX` |
| E3 | `test_generate_avoir` vérifie la référence à la facture parent |
| E4 | Les tests ne créent pas de vrais fichiers — mock uniquement |

### Sous-système F — Tests de Compilation & Sécurité (obligatoire avant chaque commit)

**Fonction** : Détecter les erreurs de syntaxe, d'import et de structure AVANT l'exécution

| # | Contrainte |
|---|---|
| F1 | `python -c "import py_compile; py_compile.compile(f, doraise=True)"` sur TOUS les .py modifiés |
| F2 | Vérifier qu'aucun `except:` sans `try:` n'a été introduit |
| F3 | Vérifier que les méthodes de classe ont la bonne indentation (4 espaces) |
| F4 | Vérifier que les contrôles Flet ne font pas `.update()` avant d'être montés |
| F5 | Vérifier que `ft.FilePicker` et autres overlays sont créés APRÈS `page.update()` |
| F6 | Lancer `pytest tests/ -v` après CHAQUE modification de code |
| F7 | Si un test échoue, ne PAS commiter — corriger d'abord |
| F8 | Le script `livrer.py` inclut l'étape de compilation dans son pipeline |

### Sous-système G — Smoke Tests (test rapide de l'UI)## 3. Code template

```python
"""Tests for ArtizBoard — <Module>."""
import pytest, uuid

@pytest.mark.django_db(transaction=True)
class Test<Feature>:
    """Tests for <feature description>."""

    def test_<action>_success(self, db_conn, etab_id, admin_id):
        """Test that <action> works with valid data."""
        # Arrange
        # Act
        # Assert
        assert result is not None

    def test_<action>_error(self, db_conn):
        """Test that <action> handles invalid input."""
        with pytest.raises(ValueError):
            # Act with bad data
            pass
```

## 4. Deux exemples

### Exemple 1 — Test simple (créer une catégorie)

```python
def test_create_category(self, db_conn, etab_id, admin_id):
    cur = db_conn.cursor()
    cid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO categories (id, nom, etablissement_id, created_by, updated_by) VALUES (%s,%s,%s,%s,%s)",
        (cid, "Test Cat", etab_id, admin_id, admin_id))
    db_conn.commit()
    cur.execute("SELECT id FROM categories WHERE nom=%s", ("Test Cat",))
    assert cur.fetchone() is not None
    # Cleanup
    cur.execute("DELETE FROM categories WHERE id=%s", (cid,))
    db_conn.commit()
    cur.close()
```

### Exemple 2 — Test avec rollback transactionnel (edge case)

```python
def test_optimistic_lock_conflict(self, db_conn, etab_id, admin_id):
    cur = db_conn.cursor()
    # Créer un produit test
    pid = str(uuid.uuid4())
    cur.execute("INSERT INTO produits (id, nom, prix, categorie_id, etablissement_id, created_by, updated_by) VALUES (%s,'Test',100,(SELECT id FROM categories LIMIT 1),%s,%s,%s)", (pid, etab_id, admin_id, admin_id))
    db_conn.commit()
    # Simuler conflit de version
    cur.execute("UPDATE produits SET prix=200, version=version+1 WHERE id=%s AND version=99", (pid,))
    assert cur.rowcount == 0  # Pas de mise à jour car version 99 n'existe pas
    db_conn.rollback()
    cur.execute("DELETE FROM produits WHERE id=%s", (pid,))
    db_conn.commit()
    cur.close()
```

## 5. Step by Step — Exécution

| Ordre | Action | Commande | Résultat |
|---|---|---|---|
| 0 | **Compilation check** | `python -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['apps/admin/__main__.py','apps/staff/__main__.py','apps/client/__main__.py']]"` | 0 erreur de syntaxe |
| 1 | Vérifier les fixtures | `pytest tests/conftest.py -v` | Fixtures OK |
| 2 | Lancer les tests existants | `pytest tests/test_auth.py tests/test_components.py tests/test_dashboard.py -v` | 64 tests baseline |
| 3 | Générer test_admin.py | Agent → `tests/test_admin.py` | 30+ tests |
| 4 | Générer test_staff.py | Agent → `tests/test_staff.py` | 20+ tests |
| 5 | Générer test_client.py | Agent → `tests/test_client.py` | 15+ tests |
| 6 | Générer test_stock.py | Agent → `tests/test_stock.py` | 10+ tests |
| 7 | Fixer test_invoice.py | Agent → mock PDF | 5 tests fixés |
| 8 | Lancer tous les tests | `pytest tests/ -v` | ~140 tests, 100% pass |

## 6. Checklist

- [ ] `test_admin.py` créé avec ≥ 30 tests
- [ ] `test_staff.py` créé avec ≥ 20 tests
- [ ] `test_client.py` créé avec ≥ 15 tests
- [ ] `test_stock.py` créé avec ≥ 10 tests
- [ ] `test_invoice.py` : 5 skipped → 5 pass
- [ ] `pytest tests/ -v` → tous verts (pas de rouge)
- [ ] Chaque test a un docstring expliquant ce qui est testé
- [ ] Les tests sont indépendants (pas de dépendance d'ordre)

## Emplacement
- Skill : `open-design/skills/test-generator/SKILL.md`
- Tests : `tests/test_admin.py`, `tests/test_staff.py`, `tests/test_client.py`, `tests/test_stock.py`
