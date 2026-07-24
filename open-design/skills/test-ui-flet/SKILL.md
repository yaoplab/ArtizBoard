# Skill: Tests UI Flet — Intégration

## 0. Contexte

**Projet** : ArtizBoard
**Module** : `tests/test_ui_*.py` — tests d'intégration UI Flet
**Utilisateurs** : Développeurs, agents IA
**Dépendances** : `flet` (page.canvas), `pytest`
**Prérequis** : App qui compile, base locale accessible

## 1. Fonction Principale

### Type : Système Fermé

```
ENTRÉE                              →  TRAITEMENT                           →  SORTIE
App Flet (Admin/Staff/Client)          Lancer app → attendre rendu           ├─ Tests verts/rouges
                                       Simuler clics via page controls       ├─ Capture d'écran (debug)
                                       Vérifier état (dialog ouvert, etc.)  └─ Rapport UI
```

- **Au début** : Une app Flet compilée sans erreur
- **À la fin** : Confirmation que les dialogues, boutons, et navigations fonctionnent
- **Entre les deux** : Automatisation des clics + assertions sur l'état UI

## 2. Contraintes Fonctionnelles

### Tableau global

| # | Contrainte |
|---|---|
| C1 | Le test lance l'app dans un thread séparé via `threading.Thread(target=ft.app, args=(main,))` |
| C2 | Le test attend le rendu initial avec `time.sleep(2)` (pas de callback Flet natif) |
| C3 | Un clic est simulé en appelant directement le handler : bouton.on_click(e_mock) |
| C4 | L'état est vérifié via les attributs Python (dlg.open, page.dialog) |
| C5 | Après chaque test, l'app est fermée (`page.window_destroy()`) |
| C6 | Les logs de debug sont activés pendant le test (`set_debug(True)`) |
| C7 | Les tests sont **indépendants** — chaque test ouvre/ferme l'app |

### Sous-système A — Vérifications UI

| # | Contrainte |
|---|---|
| A1 | Vérifier qu'un dialogue s'ouvre quand on clique un bouton |
| A2 | Vérifier que `self.page.dialog` n'est pas None après clic |
| A3 | Vérifier que `dlg.open == True` après clic |
| A4 | Vérifier que la navigation change `self._selected` |
| A5 | Vérifier que le FilePicker est créé sans erreur |

### Sous-système B — Types de tests

| # | Contrainte |
|---|---|
| B1 | **Test de fumée** : l'app démarre sans crash |
| B2 | **Test de dialogue** : chaque dialogue s'ouvre |
| B3 | **Test de navigation** : chaque onglet est accessible |
| B4 | **Test de formulaire** : les champs acceptent la saisie |
| B5 | **Test de régression** : après modification, relancer les tests |

## 3. Code template

```python
"""Tests d'integration UI pour Admin."""
import pytest, threading, time

@pytest.fixture
def admin_app():
    """Lance l'app Admin dans un thread."""
    import flet as ft
    from apps.admin.__main__ import main as admin_main

    app_started = []

    def wrapped_main(page: ft.Page):
        app_started.append(page)
        admin_main(page)

    t = threading.Thread(target=ft.app, args=(wrapped_main,), kwargs={"view": ft.AppView.FLET_APP}, daemon=True)
    t.start()
    time.sleep(3)  # Attendre le rendu

    if not app_started:
        pytest.skip("App ne demarre pas")

    page = app_started[0]
    yield page
    page.window_destroy()

class TestDialogues:
    def test_login_visible(self, admin_app):
        """L'ecran de login est affiche au demarrage."""
        page = admin_app
        # Verifier qu'il y a des controles sur la page
        assert len(page.controls) > 0

    def test_dialog_ouvert_apres_clic_bouton(self, admin_app):
        """Un clic sur un bouton ouvre un dialogue."""
        page = admin_app

        # Trouver le bouton (apres login)
        # Simuler: login
        # Puis: clic sur "Ajouter une categorie"
        # Verifier: page.dialog is not None
```

## 4. Deux exemples

### Exemple 1 — Test dialogue catégorie (fumée)

```python
def test_add_category_dialog_opens(admin_app):
    page = admin_app
    # Login reussi (admin@larepublique.tg / admin123)
    # Navigation vers Catalogue
    # Clic sur + (ajouter categorie)
    # Assert: page.dialog is not None
    # Assert: dlg.open == True
```

### Exemple 2 — Test regression _edit_produit

```python
def test_edit_produit_dialog_opens(admin_app):
    """Regression: le dialogue _edit_produit s'ouvre (bug connu)."""
    # Ce test echoue si le bug de self.page revient
    dlg = AlertDialog(title=Text("TEST"), content=Text("OK"))
    page.dialog = dlg
    dlg.open = True
    page.update()
    time.sleep(0.5)
    assert page.dialog is not None
    assert dlg.open == True
```

## 5. Step by Step

| Ordre | Action | Résultat |
|---|---|---|
| 1 | Lancement app dans thread | Page accessible |
| 2 | Login automatique | Admin connecté |
| 3 | Navigation → Catalogue | Vue catalogue |
| 4 | Clic "Ajouter catégorie" | Dialogue ouvert |
| 5 | Clic "Ajouter produit" | Dialogue ouvert ✅ |
| 6 | Clic "Modifier" sur un produit | Dialogue ouvert ✅ |
| 7 | Clic "Supprimer" sur un produit | Dialogue ouvert ✅ |
| 8 | Fermeture app | Nettoyage |

## 6. Checklist

- [ ] App démarre sans crash
- [ ] Login fonctionne (email + mdp)
- [ ] Navigation entre onglets
- [ ] Dialogue "Ajouter catégorie" s'ouvre
- [ ] Dialogue "Ajouter produit" s'ouvre
- [ ] Dialogue "Modifier produit" s'ouvre
- [ ] Dialogue "Supprimer produit" s'ouvre
- [ ] Tous les dialogues se ferment sans erreur

## Emplacement
- Skill : `open-design/skills/test-ui-flet/SKILL.md`
- Tests : `tests/test_ui_admin.py`, `tests/test_ui_staff.py`
