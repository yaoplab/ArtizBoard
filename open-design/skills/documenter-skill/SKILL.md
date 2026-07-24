# Skill: Documenter un Skill

## 0. Contexte

**Projet** : ArtizBoard
**Rôle** : Documentation — méta-skill utilisé pour créer/maintenir tous les autres skills
**Dépendances** : Aucune
**Prérequis** : Avoir un besoin fonctionnel ou technique à documenter

## 1. Fonction Principale du Système

### Type : Système Fermé

```
ENTRÉE                              TRAITEMENT                         SORTIE (×3)
┌──────────────┐    ┌─────────────────────────────────────┐    ┌──────────────┐
│ Besoin       │    │ 1. Définir fonction (ouvert/fermé)  │    │ SKILL.md     │
│ fonctionnel  │───▶│ 2. Lister contraintes par sous-sys  │───▶│ SKILL.docx   │
│ à documenter │    │ 3. Rédiger 2 exemples               │    │ dossier      │
│              │    │ 4. Appliquer tags (frontmatter)     │    │ Obsidian/    │
└──────────────┘    └─────────────────────────────────────┘    └──────────────┘
```

- **Entrée** : Un besoin métier ou technique à décrire
- **Sorties** : 3 artefacts — le `.md`, le `.docx`, le dossier Obsidian
- **Traitement** : Analyse → structuration → tagging → génération

---

## 2. Contraintes Fonctionnelles

### Tableau global — Le système de documentation

| # | Contrainte |
|---|---|
| C1 | Le skill produit **obligatoirement** 3 formats : Markdown, Word, Obsidian |
| C2 | Le fichier `.md` est la source de vérité — les autres formats en sont dérivés |
| C3 | Le fichier `.docx` est généré automatiquement depuis le `.md` via `python-docx` |
| C4 | Le dossier Obsidian contient des fichiers séparés, un par section logique |
| C5 | Chaque élément (fonction, contrainte, exemple) est **tagué** avec du YAML frontmatter |
| C6 | Les tags permettent une base de données inter-skills dans Obsidian (Dataview) |
| C7 | La fonction principale explicite clairement l'entrée, la sortie, et la transformation |

### Sous-système A — Structure des 3 formats

**Fonction** : Garantir que chaque format remplit son rôle spécifique

| # | Contrainte |
|---|---|
| A1 | Le `.md` est un fichier unique, auto-suffisant, lisible sans outil |
| A2 | Le `.docx` est identique au `.md` en contenu mais formaté pour impression/partage |
| A3 | Le dossier Obsidian éclate le contenu en fichiers atomiques liés par `[[wikilinks]]` |
| A4 | Chaque note Obsidian commence par un bloc YAML `---` définissant ses tags |
| A5 | Le dossier Obsidian contient un `index.md` qui sert de hub de navigation |
| A6 | Les noms de fichiers Obsidian sont en `kebab-case` (ex: `1-fonction.md`) |
| A7 | Le dossier final est nommé exactement comme le skill (ex: `login-paysage/`) |

### Sous-système B — Système de tags

**Fonction** : Permettre l'interopérabilité et la recherche entre skills

| # | Contrainte |
|---|---|
| B1 | Chaque note Obsidian porte les tags dans un bloc frontmatter YAML |
| B2 | Le tag principal est `skill` suivi du nom du skill : `tags: [skill, login-paysage]` |
| B3 | Les contraintes sont taguées par **type** : `contrainte`, `sous-systeme`, `exemple` |
| B4 | Les contraintes sont taguées par **importance** : `priorite-1`, `priorite-2`... |
| B5 | Les systèmes sont tagués : `systeme-ouvert` ou `systeme-ferme` |
| B6 | Les sous-systèmes héritent du tag du système parent + leur propre tag |
| B7 | Les exemples sont tagués : `exemple-simple` ou `exemple-complexe` |
| B8 | Le tag `piste-audit` est appliqué à toute note dont le contenu a été modifié |

**Résultat avec Dataview** : requêter `FROM #contrainte AND #priorite-1` → toutes les contraintes prioritaires de tous les skills.

### Sous-système C — Génération automatique

**Fonction** : Transformer le `.md` source en `.docx` + dossier Obsidian sans intervention

| # | Contrainte |
|---|---|
| C1 | Un script `generate_skill_outputs.py` prend en entrée un dossier de skill |
| C2 | Le script lit `SKILL.md`, parse les sections, génère les 2 formats supplémentaires |
| C3 | Le `.docx` utilise les styles : Titre 1, Titre 2, Normal, Code, Tableau |
| C4 | Le dossier Obsidian contient `index.md`, `1-fonction.md`, `2-contraintes.md`, `3-exemples.md` |
| C5 | Le script vérifie que tous les tags obligatoires sont présents avant de générer |
| C6 | Le script peut être exécuté sur un skill individuel ou sur tous les skills (`--all`) |
| C7 | La génération est **idempotente** — relancer écrase les sorties sans erreur |

---

## 3. Deux exemples

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
