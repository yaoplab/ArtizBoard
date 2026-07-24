---
tags:
  - skill
  - graphity
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: Le scan est **récursif** sur tout le dossier projet (hors `.venv`, `__pycache__`)
- **C2**: Chaque note Obsidian commence par un bloc YAML frontmatter avec tags
- **C3**: Les liens entre notes utilisent la syntaxe `[[nom]]` (wikilinks Obsidian)
- **C4**: La génération est **idempotente** — relancer écrase sans erreur
- **C5**: Le fichier `index.md` sert de hub central avec liens vers toutes les notes
- **C6**: Les guides utilisateur sont générés depuis les specs existantes

## [[2a-parsing-python|Sous-système A: Parsing Python]]

## [[2b-parsing-sql|Sous-système B: Parsing SQL]]

## [[2c-génération-obsidian|Sous-système C: Génération Obsidian]]

