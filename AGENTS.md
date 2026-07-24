# ArtizBoard — Instructions pour agents IA (v2.0)

## Skills & Design System
Avant toute création UI, lire ces fichiers :
- `open-design/DESIGN.md` — Design system complet (couleurs, typo, espacements)
- `open-design/skills/artizboard-m3/SKILL.md` — Règles M3 + Fibonacci
- `open-design/skills/flet-wrapper/SKILL.md` — Compatibilité Flet 0.86.x

## Flet 0.86.1 — Problèmes connus (À LIRE AVANT DE CODER)
- `ft.alignment.center` → `ft.alignment.Alignment(0,0)`
- `ft.FilledButton(text="X")` → `FilledButton(content=ft.Text("X"))`
- `ft.Card(color=...)` / `surface_tint_color=` → `bgcolor=`
- `ft.border.only()` → `ft.Border(right=Side(1,c))`
- `ft.margin.only()` → `ft.Margin(l,t,r,b)`
- `page.dialog = dlg` → `page.show_dialog(dlg)`
- `page.close_dialog()` → N'EXISTE PAS. Utiliser `dlg.open=False; page.update()`
- `ft.ImageFit.COVER` → `"cover"` (string)
- `ft.FilePicker` → NON SUPPORTÉ par flet-desktop. Utiliser champs texte
- `.update()` sur contrôle non monté → `try: control.update() except RuntimeError: pass`
- `page.window.center()` → async, utiliser tkinter pour centrer
- Toujours utiliser `ds.space_*`, jamais de pixels en dur (20, 30, 40...)
- Toujours utiliser `ds.textstyle()`, jamais `size=` + `weight=` séparés

## Règle Fondatrice

> **L'intranet local est la source unique de vérité.**
> Toute donnée de configuration est créée exclusivement en local.
> Supabase Cloud est un miroir secondaire, jamais une autorité concurrente.

## Règles générales
- Toujours lire `CONTEXT.md` avant de commencer une tâche — c'est la spec de référence
- Utiliser `ArtizBoardCommon.ds` pour TOUT le styling (ZÉRO hardcoding de couleurs/espacements)
- Utiliser `ArtizBoardCommon.components` pour les composants réutilisables (boutons, cartes, champs)
- Langue : code en anglais, UI en français, documentation en français
- UUID v4 pour tous les IDs (`import uuid; uuid.uuid4()`)
- Paths : utiliser `pathlib.Path`, jamais de chemins en dur
- **Soft delete** : jamais de CASCADE destructif, toujours utiliser `deleted_at`
- **Optimistic locking** : chaque UPDATE doit vérifier `WHERE version = X` et incrémenter `version = X + 1`
- **Audit trail** : renseigner systématiquement `created_by` et `updated_by`
- **Password** : toujours hasher avec bcrypt, jamais de stockage en clair
- **JWT local** : signé avec `SECRET_KEY` du fichier `config.ini`

## Architecture du projet
```
C:\projet\
├── CONTEXT.md                 # SPEC COMPLÈTE — lire d'abord
├── AGENTS.md                  # Ce fichier
├── pyproject.toml
├── setup.py                   # Initialisation PostgreSQL locale
├── run_admin.py               # Entry point admin (desktop)
├── run_staff.py               # Entry point staff (desktop + mobile)
├── run_client.py              # Entry point client (desktop + mobile)
├── ArtizBoardCommon\          # Design System (Flet)
│   ├── __init__.py
│   ├── config.ini             # Connexions DB locales et Supabase
│   ├── config_loader.py       # Chargeur config.ini
│   ├── design_system.py       # ds (singleton DesignSystem)
│   ├── theme.py               # tm (singleton ThemeManager)
│   ├── colors.py              # Palettes M3 (blue, dark, sobre, contrast)
│   ├── typography.py          # Échelle typographique M3
│   ├── shapes.py              # Coins arrondis, élévation
│   ├── tokens.py              # Design tokens (espacements Fibonacci)
│   ├── phi.py                 # PHI, Fibonacci, SpacingToken
│   ├── components.py          # Composants M3 Flet (boutons, cartes, champs)
│   ├── icons.py               # Constantes d'icônes
│   └── AGENTS.md              # Instructions design system
├── apps\                      # Applications par rôle
│   ├── common\                # Partagé (auth, login)
│   │   ├── auth.py            # bcrypt, JWT, activation codes
│   │   └── login.py           # Login paysage (HeroPanel + LoginForm)
│   ├── admin\                 # App Admin (Flet) — Livrable D
│   │   └── __main__.py        # python -m apps.admin
│   ├── staff\                 # App Staff (Flet mobile) — Livrable E
│   │   └── __main__.py
│   └── client\                # Portail Client (Flet) — Livrable E
│       └── __main__.py
├── build\                     # Scripts de compilation
│   ├── build_admin_desktop.bat
│   ├── build_staff_desktop.bat
│   └── build_client_desktop.bat
├── db\                        # Scripts SQL — Livrable A
│   ├── migrations\
│   ├── init_pg_local.sql
│   ├── init_supabase.sql
│   └── pgbouncer.ini
├── sync_service.py            # Synchro locale ↔ Cloud — Livrable A
├── deploy_site.py              # Déploiement WordPress sur Hostinger — Livrable G
├── seed_pages.py               # Seed des pages établissement (exemples)
├── invoice_generator.py        # Factures PDF + ESC/POS — Livrable B
├── dashboard_manager.py        # Dashboard & Export — Livrable C
├── wp-content\               # Thème WordPress (pour Hostinger)
│   └── themes\
│       └── artizboard\        # Thème public connecté à Supabase
├── site_public\               # Version statique HTML/CSS (alternative)
├── tests\                     # Tests pytest
└── backups\                   # Dumps PostgreSQL locaux
```

## Commandes
```bash
cd C:\projet

# Développement
python -m apps.admin          # App Admin
python -m apps.staff          # App Staff
python -m apps.client         # Portail Client
python run_admin.py           # Alternative directe
python run_staff.py
python run_client.py

# Compilation autonome
cd build
build_admin_desktop.bat       # → ArtizBoard Admin.exe
build_staff_desktop.bat       # → ArtizBoard Staff.exe
build_client_desktop.bat      # → ArtizBoard Client.exe

# Compilation mobile (tablette)
flet build apk ..\run_staff.py --name "ArtizBoard Staff"
flet build apk ..\run_client.py --name "ArtizBoard Client"

# Tests
pytest tests/ -v

# Sync service
python sync_service.py

# Déploiement site WordPress
python deploy_site.py          # Build + Upload FTP + Config WordPress
```

## Conventions de code

### Imports standards
```python
import flet as ft
import uuid
from pathlib import Path
from decimal import Decimal
from ArtizBoardCommon import ds, tm, icons
from ArtizBoardCommon.components import button, card, textfield, kpi_card, spacer
from ArtizBoardCommon.components import ButtonVariant, CardVariant, Severity
```

### Design System
```python
# Couleurs
ds.p.primary, ds.p.on_primary, ds.p.surface, ds.p.error
ds.p.text_strong, ds.p.text_soft, ds.p.text_disabled

# Espacements Fibonacci (base 4)
ds.space_xxs  # 4px
ds.space_xs   # 8px
ds.space_sm   # 12px
ds.space_md   # 20px
ds.space_lg   # 32px
ds.space_xl   # 52px
ds.space_xxl  # 84px

# Typographie
style=ds.textstyle("headline_medium")
style=ds.textstyle("title_large")
style=ds.textstyle("body_medium")
style=ds.textstyle("label_small")

# Formes
border_radius=ds.border_radius(ds.SHAPE_MD)  # 12px
border_radius=ds.border_radius(ds.SHAPE_SM)  # 8px
border_radius=ds.border_radius(ds.SHAPE_FULL)  # pill

# Proportions
large, small = ds.golden_split(page.width)

# Thèmes
ds.switch_theme("dark")
ds.apply(page)  # Applique ft.Theme à la page
```

### Composants M3
```python
# Boutons (filled, tonal, outlined, text, elevated)
button("Valider", variant=ButtonVariant.FILLED, icon=ft.Icons.CHECK, on_click=handler)

# Cartes (elevated, filled, outlined)
card("Titre", content=ft.Text("Contenu"), variant=CardVariant.ELEVATED)

# Champs texte
textfield(label="Email", value="", hint="nom@exemple.com", prefix_icon="email")

# KPI Card
kpi_card("1 200 000 CFA", "Chiffre d'affaires", icon="trending_up")

# Dialogues
dialog(titre, contenu, actions=[bouton1, bouton2])
confirm_dialog("Supprimer ?", "Cette action est irreversible", on_confirm=handler)

# Snackbar, Banner, Badge
snackbar("Operation reussie", severity=Severity.SUCCESS)
banner("Erreur de connexion", severity=Severity.ERROR)
badge("3", severity=Severity.WARNING)
```

### Connexion DB
```python
# Local (PostgreSQL direct ou PgBouncer)
from ArtizBoardCommon.config_loader import get_db_config, get_supabase_config
db = get_db_config()           # → (host, port, name, user, password)
supabase = get_supabase_config()  # → (url, anon_key, service_role_key)
```

### Pattern CRUD (avec soft delete + locking)
```python
def update_produit(produit_id: uuid.UUID, data: dict, modified_by: uuid.UUID):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE produits
            SET nom = %s, prix = %s, updated_at = NOW(),
                updated_by = %s, version = version + 1
            WHERE id = %s AND version = %s AND deleted_at IS NULL
            RETURNING version
        """, (data["nom"], data["prix"], modified_by, produit_id, data["version"]))
        if cur.rowcount == 0:
            raise ConcurrentModificationError("Produit modifié par un autre utilisateur")

def soft_delete(table: str, id: uuid.UUID, deleted_by: uuid.UUID):
    cur.execute(f"""
        UPDATE {table} SET deleted_at = NOW(), updated_by = %s
        WHERE id = %s AND deleted_at IS NULL
    """, (deleted_by, id))
```

---

## Règles Métier

### Sync
- Config → montée uniquement (Local → Cloud)
- Commandes client internet → descente (Cloud → Local)
- Pas de conflit sur les configs
- `sync_status` : local → pending → synced
- Mode 100% intranet : `sync_enabled = false` dans `config.ini`

### Auth
- QR code (recommandé) ou code manuel (fallback)
- Token 16 caractères hex, hashé SHA-256, 5 minutes, 3 tentatives
- JWT signé localement, refresh token pour rotation
- Fallback auto auth locale si Supabase injoignable

### Activation
- Admin génère le code depuis l'interface Admin (jamais depuis le cloud)
- `POST /api/activate` reçoit { token, device_name, device_ip }
- Stocke dans `activation_codes` et `devices`

### Factures
- Format normal : `FAC-YYYYMMDD-XXXXX` (SEQUENCE PostgreSQL)
- Format déconnecté : `FAC-YYYYMMDD-DEV{ID}-XXXXX` (renuméroté à la synchro)
- Type : `facture` ou `avoir` (note de crédit)
- Impression : ESC/POS via python-escpos, envoyé par le serveur local

### Paiement
- Interface abstraite `PaymentGateway` avec 3 implémentations
- Simulée pour le développement, TMoney/Flooz pour la prod

### Backup
- Rétention 4-4-1, chiffré AES-256, checksum SHA-256
- Restauration avec validation checksum

---

## Livrables (ordre de réalisation)

| # | Livrable | Contenu | Statut |
|---|---|---|---|
| A | BDD & Synchro | `db/`, `sync_service.py`, config PgBouncer | ✅ |
| B | Facturation | `invoice_generator.py` (ReportLab + ESC/POS) | ✅ |
| C | Dashboard | `dashboard_manager.py` (KPIs, CSV, PDF) | ✅ |
| D | App Admin | `apps/admin/` (login, dashboard, catalogue, users, backup) | ✅ |
| E | Client & Staff | `apps/staff/` + `apps/client/` (mobile, QR, KDS, panier) | ✅ |
| F | Site Web Public | `wp-content/themes/artizboard/` → Hostinger, `deploy_site.py` | ✅ |
| G | Pages Établissement | `pages_etablissement` + UI Admin + rendu WordPress | ✅ |
| H | Templates modernes | 10 presets theme_config (5 resto + 5 boutique) | ✅ |
| I | Documentation | 11 skills × 3 formats, graphity, Obsidian | ✅ |
| J | Déploiement | FTP, WordPress API, Supabase keys injection | ✅ |

## Skills disponibles (11)

| Skill | Rôle | Format |
|---|---|---|
| `documenter-skill` | 🔧 Méta-skill : comment créer/maintenir un skill | 10/10 ✅ |
| `design-system` | 🎨 Design system M3 + Fibonacci | 10/10 ✅ |
| `artizboard-m3` | 🖌️ Règles UI strictes (anti-patterns) | 10/10 ✅ |
| `flet-wrapper` | 🛠️ Compatibilité Flet 0.86 | 10/10 ✅ |
| `wordpress-theme` | 🌐 WordPress + Supabase + Hostinger | 10/10 ✅ |
| `login-paysage` | 🔑 Écran login golden split | 10/10 ✅ |
| `auth-locale` | 🔒 bcrypt, JWT, QR activation | 10/10 ✅ |
| `catalogue-3panels` | 📋 CRUD catalogue master-detail | 10/10 ✅ |
| `crud-m3` | 🗄️ Soft delete + optimistic lock | 10/10 ✅ |
| `kds-kanban` | 🍳 Kitchen Display System | 10/10 ✅ |
| `graphity` | 📊 Graphe code → Obsidian | 10/10 ✅ |

## Site Web — WordPress

- Thème actif sur https://aristodetoonasi.com
- Dernier déploiement : `python deploy_site.py`
- 10 templates prêts : Admin → Établissement → Apparence → sélecteur de preset
- Clés Supabase format `sb_publishable_...` / `sb_secret_...`
- Si HTML/CSS cassé : `python graphity.py` génère le vault Obsidian pour diagnostiquer

## WordPress — Règles spécifiques

- Le thème est dans `wp-content/themes/artizboard/` (PHP + CSS + JS)
- Les données viennent de **Supabase** via le SDK JS (pas de données métier dans WordPress)
- Les clés Supabase dans `config.js` utilisent le format `sb_publishable_...` (pas JWT)
- Le fichier `page.php` est universel — il détecte le slug et rend le bon onglet
- Pour que les pages WordPress fonctionnent : `index.php` doit exister à la racine `public_html/`
- Si le REST API est bloqué : installer **Classic Editor** et vérifier les permaliens
- Pour déployer : `python deploy_site.py` (lit `[hostinger]` dans `config.ini`)
- Licence : MIT — voir `LICENSE` à la racine

## Licence MIT

ArtizBoard est sous licence MIT. Cela signifie :
- **✅ Droit d'utiliser** gratuitement, y compris commercialement
- **✅ Droit de modifier** et redistribuer le code source
- **✅ Droit d'inclure** dans des logiciels propriétaires
- **⚠️ Pas de garantie** — le logiciel est fourni "en l'état"
- **ℹ️ Conservation** de la notice de copyright obligatoire

## Tests
- pytest dans `tests/`
- Mocker Supabase pour tests offline
- Tests unitaires pour chaque module
- Tests de charge Flet (simuler 50+ sessions)
