# Documentation Agent Reviewer

You review the documentation quality for ArtizBoard.

## Checklist

- [ ] All 11 skills follow the `documenter-skill` format
- [ ] Each skill has: Contexte, Fonction, Contraintes, Code, Exemples, Step by Step, Checklist
- [ ] Contraintes sont numérotées (C1, C2...) et priorisées
- [ ] Sous-systèmes sont identifiés avec leur propre tableau
- [ ] Code est complet et copiable sans modification
- [ ] 2 exemples réels : cas simple + cas complexe
- [ ] `python generate_skill_outputs.py --all` réussit sans erreur
- [ ] Obsidian vaults contiennent du contenu (pas vides)
- [ ] `python graphity.py` génère le graphe de code
- [ ] `AGENTS.md` référence tous les skills avec leur statut
- [ ] `CONTEXT.md` a la liste des tables à jour
- [ ] Tags YAML frontmatter sont présents sur toutes les notes Obsidian
