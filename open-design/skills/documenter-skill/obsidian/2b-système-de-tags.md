---
tags:
  - skill
  - documenter-skill
  - contrainte
  - sous-systeme
  - priorite-1
---

# Sous-système B: Système de tags

- **B1**: Chaque note Obsidian porte les tags dans un bloc frontmatter YAML
- **B2**: Le tag principal est `skill` suivi du nom du skill : `tags: [skill, login-paysage]`
- **B3**: Les contraintes sont taguées par **type** : `contrainte`, `sous-systeme`, `exemple`
- **B4**: Les contraintes sont taguées par **importance** : `priorite-1`, `priorite-2`...
- **B5**: Les systèmes sont tagués : `systeme-ouvert` ou `systeme-ferme`
- **B6**: Les sous-systèmes héritent du tag du système parent + leur propre tag
- **B7**: Les exemples sont tagués : `exemple-simple` ou `exemple-complexe`
- **B8**: Le tag `piste-audit` est appliqué à toute note dont le contenu a été modifié
