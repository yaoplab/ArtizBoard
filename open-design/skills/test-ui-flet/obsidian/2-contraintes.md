---
tags:
  - skill
  - test-ui-flet
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: Le test lance l'app dans un thread séparé via `threading.Thread(target=ft.app, args=(main,))`
- **C2**: Le test attend le rendu initial avec `time.sleep(2)` (pas de callback Flet natif)
- **C3**: Un clic est simulé en appelant directement le handler : bouton.on_click(e_mock)
- **C4**: L'état est vérifié via les attributs Python (dlg.open, page.dialog)
- **C5**: Après chaque test, l'app est fermée (`page.window_destroy()`)
- **C6**: Les logs de debug sont activés pendant le test (`set_debug(True)`)
- **C7**: Les tests sont **indépendants** — chaque test ouvre/ferme l'app

## [[2a-vérifications-ui|Sous-système A: Vérifications UI]]

## [[2b-types-de-tests|Sous-système B: Types de tests]]

