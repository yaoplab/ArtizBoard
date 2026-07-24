# Skill: Licence & Droits d'Usage

## 0. Contexte

**Projet** : ArtizBoard
**Module** : Toutes les apps + site web + documentation
**Utilisateurs** : Développeurs, Admin, Staff, Clients
**Dépendances** : [[wordpress-theme]], [[design-system]]
**Prérequis** : Licence choisie (MIT, Apache 2.0, GPL...)

## 1. Fonction Principale

### Type : Système Fermé

```
ENTRÉE                              →  TRAITEMENT                           →  SORTIE
Licence choisie (MIT)                  Appliquer les règles à chaque app      ├─ Page Licence dans le site web
                                       Injecter copyright dans footer          ├─ Mention dans apps Admin/Staff/Client
                                       Ajouter LICENSE fichier                 └─ Documentation mise à jour
```

- **Au début** : Une licence open-source est sélectionnée (MIT par défaut)
- **À la fin** : Tous les points de contact utilisateur affichent les droits et obligations
- **Entre les deux** : Traduction juridique → langage simple → intégration UI

## 2. Contraintes Fonctionnelles

### Tableau global — Toute app affiche la licence

| # | Contrainte |
|---|---|
| C1 | Le fichier `LICENSE` à la racine contient le texte juridique complet (anglais) |
| C2 | Chaque app (Admin, Staff, Client) a une page ou un dialogue "À propos / Licence" |
| C3 | Le site web a une page `/licence` accessible depuis le footer |
| C4 | Toute mention de copyright inclut "© 2026 ArtizBoard — Licence MIT" |
| C5 | Les droits et obligations sont expliqués en **langage simple** (pas de jargon juridique) |
| C6 | Les 3 catégories sont clairement séparées : ✅ Droits, ℹ️ Conditions, ⚠️ Garantie |

### Sous-système A — Contenu de la page licence

**Fonction** : Expliquer simplement ce que MIT permet et interdit

| # | Contrainte |
|---|---|
| A1 | Section "✅ Droits accordés" : utiliser, copier, modifier, vendre, intégrer |
| A2 | Section "ℹ️ Conditions" : conserver le copyright, inclure la notice |
| A3 | Section "⚠️ Garantie" : logiciel fourni "en l'état", pas de responsabilité |
| A4 | Lien vers le texte officiel : https://opensource.org/licenses/MIT |
| A5 | Format lisible, pas de bloc de texte brut — utiliser listes et icônes |

### Sous-système B — Intégration dans les apps Flet

**Fonction** : Chaque app desktop/mobile affiche les infos de licence

| # | Contrainte |
|---|---|
| B1 | Admin : lien "À propos / Licence" dans le menu latéral ou info en bas |
| B2 | Staff : mention dans l'écran de connexion |
| B3 | Client : footer "Propulsé par ArtizBoard — MIT" |
| B4 | Le dialogue Admin "À propos" liste : version, licence, auteur, lien GitHub |

### Sous-système C — Différentes licences supportées

**Fonction** : Le skill doit pouvoir s'adapter si la licence change

| # | Contrainte |
|---|---|
| C1 | MIT : permissif — tout autorisé, juste garder le copyright |
| C2 | Apache 2.0 : permissif + brevet + notice des modifications |
| C3 | GPLv3 : copyleft — redistribuer sous la même licence, code source obligatoire |
| C4 | La licence est définie dans `config.ini` sous `[app] licence = MIT` |
| C5 | Le script `apply_licence.py` lit la licence et met à jour tous les fichiers |

## 3. Mapping par licence

### MIT (actuel)

| Catégorie | Contenu |
|---|---|
| ✅ Peut | Utiliser, copier, modifier, distribuer, vendre, inclure dans du propriétaire |
| ℹ️ Doit | Garder la notice de copyright + permission dans les copies |
| ⚠️ Pas de | Garantie, responsabilité des auteurs |

### Apache 2.0 (si changement)

| Catégorie | Contenu |
|---|---|
| ✅ Peut | Tout MIT + protection des brevets |
| ℹ️ Doit | Tout MIT + indiquer les modifications apportées |
| ⚠️ Pas de | Tout MIT |

### GPLv3 (si changement)

| Catégorie | Contenu |
|---|---|
| ✅ Peut | Utiliser, modifier, distribuer |
| ℹ️ Doit | Redistribuer sous GPL, fournir le code source, documenter les changements |
| ⚠️ Pas de | Intégration dans du propriétaire sans ouvrir le code |

## 4. Deux exemples

### Exemple 1 — Canvas "Droits et Devoirs" pour MIT (cas simple)

```
┌──────────────────────────────────────────────────────────┐
│                      LICENCE MIT                         │
├─────────────────┬──────────────────┬─────────────────────┤
│   ✅ VOUS POUVEZ  │  ℹ️ VOUS DEVEZ    │  ⚠️ ATTENTION       │
├─────────────────┼──────────────────┼─────────────────────┤
│ Utiliser          │ Conserver le     │ Pas de garantie     │
│ Modifier          │   copyright      │ Pas de              │
│ Distribuer        │ Inclure la       │   responsabilité    │
│ Vendre            │   notice         │ Logiciel "en l'état"│
│ Intégrer          │                  │                     │
└─────────────────┴──────────────────┴─────────────────────┘
```

### Exemple 2 — Page WordPress `/licence` (cas complexe)

La page licence doit :
1. Être créée automatiquement ou manuellement via `template-licence.php`
2. Être accessible depuis le footer du site (`/licence`)
3. Afficher le contenu de la licence dans la langue du site (français)
4. Contenir un lien vers opensource.org pour le texte officiel
5. Être responsive et suivre le design system M3

## 5. Step by Step — Implémentation

| Ordre | Action | Fichier | Résultat |
|---|---|---|---|
| 1 | Créer `LICENSE` à la racine | `LICENSE` | Texte juridique MIT |
| 2 | Créer `template-licence.php` | `wp-content/themes/artizboard/` | Page WordPress |
| 3 | Ajouter lien dans `footer.php` | `wp-content/themes/artizboard/` | Lien vers /licence |
| 4 | Mettre à jour `AGENTS.md` | `AGENTS.md` | Section Licence |
| 5 | Ajouter dialogue Admin | `apps/admin/__main__.py` | Menu → À propos |
| 6 | Mettre à jour footer apps | `apps/admin/`, `staff/`, `client/` | Copyright visible |
| 7 | Régénérer ZIP et déployer | `deploy_site.py` | Site à jour |

## 6. Checklist

- [ ] Fichier `LICENSE` présent à la racine
- [ ] Page `/licence` sur le site WordPress
- [ ] Footer site : lien vers licence + "Propulsé par ArtizBoard"
- [ ] Admin : info licence accessible (menu ou footer)
- [ ] Staff : mention licence dans l'écran de connexion
- [ ] Client : footer avec copyright
- [ ] AGENTS.md : section Licence documentée
- [ ] Tous les `.docx` régénérés avec `generate_skill_outputs.py --all`

## Emplacement
- Licence : `LICENSE` (racine)
- Page web : `wp-content/themes/artizboard/template-licence.php`
- Dialogues apps : `apps/admin/__main__.py`, `apps/staff/__main__.py`, `apps/client/__main__.py`
- Script auto : `apply_licence.py`
