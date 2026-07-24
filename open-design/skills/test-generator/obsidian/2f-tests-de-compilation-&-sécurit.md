---
tags:
  - skill
  - test-generator
  - contrainte
  - sous-systeme
  - priorite-2
---

# Sous-système F: Tests de Compilation & Sécurité (obligatoire avant chaque commit)

- **F1**: `python -c "import py_compile; py_compile.compile(f, doraise=True)"` sur TOUS les .py modifiés
- **F2**: Vérifier qu'aucun `except:` sans `try:` n'a été introduit
- **F3**: Vérifier que les méthodes de classe ont la bonne indentation (4 espaces)
- **F4**: Vérifier que les contrôles Flet ne font pas `.update()` avant d'être montés
- **F5**: Vérifier que `ft.FilePicker` et autres overlays sont créés APRÈS `page.update()`
- **F6**: Lancer `pytest tests/ -v` après CHAQUE modification de code
- **F7**: Si un test échoue, ne PAS commiter — corriger d'abord
- **F8**: Le script `livrer.py` inclut l'étape de compilation dans son pipeline
