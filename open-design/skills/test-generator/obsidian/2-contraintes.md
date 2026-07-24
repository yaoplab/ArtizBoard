---
tags:
  - skill
  - test-generator
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: Chaque module a son fichier de test : `test_admin.py`, `test_staff.py`, `test_client.py`, `test_stock.py`
- **C2**: Chaque test est une méthode `test_xxx` dans une classe `TestXxx`
- **C3**: Les fixtures sont réutilisées depuis `conftest.py` : `db_conn`, `cur`, `admin_id`, `etab_id`, `auth`
- **C4**: Les tests de DB utilisent des transactions qui font rollback après chaque test
- **C5**: Les tests UI (Flet) sont `skip` avec motif `"UI test requires display"`
- **C6**: Chaque fonctionnalité critique a un test : création, lecture, modification, suppression (CRUD)
- **C7**: Chaque test vérifie : succès nominal + au moins 1 cas d'erreur
- **C8**: Les tests sont **indépendants** — l'ordre d'exécution n'importe pas
- **C9**: Le ratio minimum est de **2 tests par endpoint/méthode publique**

## [[2a-test-admin|Sous-système A: Test Admin]]

## [[2b-test-staff|Sous-système B: Test Staff]]

## [[2c-test-client|Sous-système C: Test Client]]

## [[2d-test-stock|Sous-système D: Test Stock]]

## [[2e-test-invoice-(fix-skip)|Sous-système E: Test Invoice (fix skip)]]

## [[2f-tests-de-compilation-&-sécurit|Sous-système F: Tests de Compilation & Sécurité (obligatoire avant chaque commit)]]

## [[2g-smoke-tests-(test-rapide-de-l'|Sous-système G: Smoke Tests (test rapide de l'UI)## 3. Code template]]

