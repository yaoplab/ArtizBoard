---
tags:
  - skill
  - documenter-skill
  - contrainte
---

# Contraintes Fonctionnelles

## Tableau global

- **C1**: Le skill produit **obligatoirement** 3 formats : Markdown, Word, Obsidian
- **C2**: Le fichier `.md` est la source de vérité — les autres formats en sont dérivés
- **C3**: Le fichier `.docx` est généré automatiquement depuis le `.md` via `python-docx`
- **C4**: Le dossier Obsidian contient des fichiers séparés, un par section logique
- **C5**: Chaque élément (fonction, contrainte, exemple) est **tagué** avec du YAML frontmatter
- **C6**: Les tags permettent une base de données inter-skills dans Obsidian (Dataview)
- **C7**: La fonction principale explicite clairement l'entrée, la sortie, et la transformation

## [[2a-structure-des-3-formats|Sous-système A: Structure des 3 formats]]

## [[2b-système-de-tags|Sous-système B: Système de tags]]

## [[2c-génération-automatique|Sous-système C: Génération automatique]]

