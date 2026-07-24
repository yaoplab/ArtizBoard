---
tags:
  - skill
  - documenter-skill
  - contrainte
  - sous-systeme
  - priorite-2
---

# Sous-système C: Génération automatique

- **C1**: Un script `generate_skill_outputs.py` prend en entrée un dossier de skill
- **C2**: Le script lit `SKILL.md`, parse les sections, génère les 2 formats supplémentaires
- **C3**: Le `.docx` utilise les styles : Titre 1, Titre 2, Normal, Code, Tableau
- **C4**: Le dossier Obsidian contient `index.md`, `1-fonction.md`, `2-contraintes.md`, `3-exemples.md`
- **C5**: Le script vérifie que tous les tags obligatoires sont présents avant de générer
- **C6**: Le script peut être exécuté sur un skill individuel ou sur tous les skills (`--all`)
- **C7**: La génération est **idempotente** — relancer écrase les sorties sans erreur
