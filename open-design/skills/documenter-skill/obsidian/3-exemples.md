---
tags:
  - skill
  - documenter-skill
  - exemple
---

# Exemples

### Exemple 1 — Cas simple : Skill `auth-locale`

**Tags appliqués :**
```yaml
---
tags: [skill, auth-locale, systeme-ferme, priorite-1]
---
```

**Fichiers Obsidian générés :**
```
auth-locale/
├── index.md            ← tags: [hub, auth-locale]
├── 1-fonction.md       ← tags: [fonction, auth-locale, systeme-ferme]
├── 2-contraintes.md    ← tags: [contrainte, auth-locale]
├── 2a-hash-password.md ← tags: [contrainte, sous-systeme, auth-locale, priorite-2]
├── 2b-jwt.md           ← tags: [contrainte, sous-systeme, auth-locale, priorite-2]
├── 2c-qr-activation.md ← tags: [contrainte, sous-systeme, auth-locale, priorite-3]
├── 3-exemples.md       ← tags: [exemple, auth-locale]
└── 3a-login.md         ← tags: [exemple, auth-locale, exemple-simple]
```

### Exemple 2 — Cas complexe : Skill `graphity`

**Contexte** : Skill qui scanne le code et génère lui-même un vault Obsidian. Montre la récursivité du système de tags.

**Tags appliqués :**
```yaml
---
tags: [skill, graphity, systeme-ouvert, priorite-1, meta-skill]
---
```

**Fichiers Obsidian générés :**
```
graphity/
├── index.md                ← tags: [hub, graphity, meta-skill]
├── 1-fonction.md           ← tags: [fonction, graphity, systeme-ouvert]
├── 2-contraintes.md        ← tags: [contrainte, graphity]
├── 2a-parsing.md           ← tags: [contrainte, sous-systeme, graphity, priorite-1]
├── 2b-generation.md        ← tags: [contrainte, sous-systeme, graphity, priorite-2]
├── 2c-guides.md            ← tags: [contrainte, sous-systeme, graphity, priorite-3]
├── 3-exemples.md           ← tags: [exemple, graphity]
├── 3a-obsidian-vault.md    ← tags: [exemple, graphity, exemple-simple]
└── 3b-dataview-query.md    ← tags: [exemple, graphity, exemple-complexe]
```

**Exemple de requête Dataview entre skills :**
```dataview
TABLE tags, sous-systeme
FROM #contrainte AND #priorite-1
SORT file.name ASC
```
→ Affiche toutes les contraintes de priorité 1, tous skills confondus.

---

## Tags standardisés

Liste exhaustive des tags utilisables. Chaque skill DOIT utiliser au moins ceux marqués *.

| Catégorie | Tag | Description |
|---|---|---|
| **Type** | `skill` | Obligatoire — identifie un document de skill |
| **Nom** | `nom-du-skill` | Obligatoire — identifiant unique du skill |
| **Système** | `systeme-ouvert` | Le système a des entrées/sorties non bornées |
| **Système** | `systeme-ferme` | Le système a des entrées/sorties exactes |
| **Nature** | `fonction` | Décrit la fonction principale |
| **Nature** | `contrainte` | Une règle que le système doit respecter |
| **Nature** | `sous-systeme` | Une partie décomposée du système |
| **Nature** | `exemple` | Un cas d'usage illustratif |
| **Nature** | `hub` | Fichier index de navigation |
| **Priorité** | `priorite-1` | Critique — le système ne fonctionne pas sans |
| **Priorité** | `priorite-2` | Important — dégradation partielle si absent |
| **Priorité** | `priorite-3` | Souhaitable — confort mais pas bloquant |
| **Exemple** | `exemple-simple` | Cas nominal, chemin heureux |
| **Exemple** | `exemple-complexe` | Edge case, scénario avancé |
| **Audit** | `piste-audit` | Contenu modifié depuis la dernière génération |
| **Méta** | `meta-skill` | Le skill lui-même porte sur la documentation |

---

## 5. Step by Step — Implémentation

| Ordre | Action | Fichier | Résultat |
|---|---|---|---|
| 1 | Créer le dossier du skill | `open-design/skills/<nom>/` | Dossier vide |
| 2 | Rédiger la fonction principale (section 1) | `SKILL.md` | Entrée → Sortie définies |
| 3 | Lister les contraintes globales (tableau C1..Cn) | `SKILL.md` | Contraintes priorisées |
| 4 | Décomposer en sous-systèmes (tableaux A, B, C...) | `SKILL.md` | Sous-fonctions isolées |
| 5 | Rédiger le code complet (section 3) | `SKILL.md` | Code copiable sans modif |
| 6 | Ajouter 2 exemples réels (section 4) | `SKILL.md` | Cas simple + cas complexe |
| 7 | Générer les 3 formats | `python generate_skill_outputs.py <nom>` | `.md` + `.docx` + Obsidian |
| 8 | Valider avec la checklist | `SKILL.md` | Tous les ✓ cochés |

## 6. Checklist de validation

- [ ] Fonction principale décrite (entrée → traitement → sortie)
- [ ] 3 formats produits : `.md`, `.docx`, dossier Obsidian
- [ ] Toutes les notes Obsidian ont un bloc frontmatter YAML avec tags
- [ ] Tags obligatoires présents : `skill`, `nom-du-skill`, `systeme-*`
- [ ] Contraintes numérotées (C1, C2...) et taguées par priorité
- [ ] 2 exemples réels avec contextes différents
- [ ] `python generate_skill_outputs.py <nom-du-skill>` s'exécute sans erreur
- [ ] Le dossier Obsidian peut être ouvert comme vault autonome

## Emplacement
- Skill template : `open-design/skills/documenter-skill/SKILL.md`
- Générateur : `generate_skill_outputs.py` (racine)
- Sortie `.docx` : `open-design/skills/<nom>/<nom>.docx`
- Sortie Obsidian : `open-design/skills/<nom>/obsidian/`