# Skill: Graphity — Analyse structurelle du code

## Purpose
Analyser la structure d'un fichier Python avant toute édition pour éviter les bugs.
Obligatoire avant de modifier `apps/admin/__main__.py` (2799 lignes, 98 méthodes).

## Usage
```bash
# Vue d'ensemble
python graphity.py

# Une méthode spécifique (affiche le code)
python graphity.py -m _dashboard_content

# Lister les wrappers legacy à migrer
python graphity.py --legacy
```

## Output
```
__main__.py | 2799 lignes | 4 classes | 98 méthodes | modifié 00:49
Legacy: 80 | Raw Flet: 148

class AdminApp L57 (9 méthodes)
  .__init__() L60 [10l] -> _conn, get_db_config
  .run() L83 [35l] -> _show_login, _show_dashboard

class DashboardScreen L380 (73 méthodes)
  ._dashboard_content() L508 [236l] -> dm.get_kpis, ana_refresh
  ._edit_produit() L1244 [75l] -> ft.TextField, show_dialog
  ...
```

## Règles avant édition
1. Toujours lancer `python graphity.py` avant de modifier un fichier
2. Si une méthode fait >50 lignes → lire juste cette méthode avec `-m NOM`
3. Si legacy >0 → vérifier que la méthode utilise du Flet natif, pas les wrappers
4. Après édition → relancer graphity pour vérifier que rien n'est cassé (compter les méthodes)

## Structure actuelle (admin)
- 4 classes: AdminApp, FirstBootScreen, LoginScreen, DashboardScreen
- 98 méthodes, 80 wrappers legacy restants, 148 utilisations Flet natives

## Emplacement
`C:\projet\graphity.py`
