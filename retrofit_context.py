"""Retrofit Context + Step by Step to all SKILL.md files."""
from pathlib import Path
import re

SKILLS_DIR = Path(__file__).parent / "open-design" / "skills"

# Per-skill context data (fill in what we know)
CONTEXTS = {
    "login-paysage": "**Projet** : ArtizBoard\n**Module** : `apps/common/login.py` — écran de connexion\n**Utilisateurs** : Admin (desktop), Staff (mobile), Client (web)\n**Dépendances** : [[design-system]], [[artizboard-m3]], [[flet-wrapper]]\n**Prérequis** : Design System chargé (`ds.apply(page)`)",
    "auth-locale": "**Projet** : ArtizBoard\n**Module** : `apps/common/auth.py` — authentification locale\n**Utilisateurs** : Admin (gère), Staff (s'authentifie)\n**Dépendances** : [[crud-m3]] (pour la DB), `config.ini` (SECRET_KEY)\n**Prérequis** : PostgreSQL local + table `utilisateurs` créée",
    "catalogue-3panels": "**Projet** : ArtizBoard\n**Module** : `apps/admin/__main__.py` — gestion du catalogue\n**Utilisateurs** : Admin\n**Dépendances** : [[crud-m3]], [[design-system]], `categories` + `produits` (DB)\n**Prérequis** : Établissement créé, catégories seedées",
    "crud-m3": "**Projet** : ArtizBoard\n**Module** : Patterns DB — toutes les apps\n**Utilisateurs** : Admin, Staff\n**Dépendances** : PostgreSQL, soft delete, UUID\n**Prérequis** : Connexion DB via PgBouncer",
    "kds-kanban": "**Projet** : ArtizBoard\n**Module** : `apps/staff/__main__.py` — écran cuisine\n**Utilisateurs** : Cuisinier (Staff)\n**Dépendances** : [[auth-locale]], `commandes` + `lignes_commande` (DB)\n**Prérequis** : Staff connecté, commandes en cours",
    "graphity": "**Projet** : ArtizBoard\n**Module** : `graphity.py` — générateur de documentation\n**Utilisateurs** : Développeurs, agents IA\n**Dépendances** : [[documenter-skill]]\n**Prérequis** : Codebase à scanner",
    "wordpress-theme": "**Projet** : ArtizBoard\n**Module** : `wp-content/themes/artizboard/` — site public\n**Utilisateurs** : Clients (navigateur), Admin (déploiement)\n**Dépendances** : Supabase, Hostinger, WordPress\n**Prérequis** : Supabase sync actif, Hostinger configuré",
    "design-system": "**Projet** : ArtizBoard\n**Module** : `ArtizBoardCommon/` — système de design global\n**Utilisateurs** : Tous les développeurs\n**Dépendances** : Aucune\n**Prérequis** : `pip install flet`",
    "artizboard-m3": "**Projet** : ArtizBoard\n**Module** : `ArtizBoardCommon/` — règles UI\n**Utilisateurs** : Tous les développeurs\n**Dépendances** : [[design-system]]\n**Prérequis** : Design System appliqué (`ds.apply(page)`)",
    "flet-wrapper": "**Projet** : ArtizBoard\n**Module** : `ArtizBoardCommon/ftw.py` — compatibilité Flet 0.86\n**Utilisateurs** : Tous les développeurs\n**Dépendances** : [[design-system]]\n**Prérequis** : Flet 0.86.x installé",
    "documenter-skill": "**Projet** : ArtizBoard\n**Module** : `open-design/skills/documenter-skill/` — méta-skill\n**Utilisateurs** : Développeurs, agents IA\n**Dépendances** : Aucune\n**Prérequis** : Besoin à documenter",
}

STEPS = {
    "login-paysage": "| 1 | Créer HeroPanel avec gradient | `apps/common/login.py` | Panel gauche rendu |\n| 2 | Créer LoginForm avec champs + QR | `apps/common/login.py` | Formulaire droit rendu |\n| 3 | Assembler avec golden split | `apps/common/login.py` | Layout 62/38% |\n| 4 | Intégrer dans l'app (Admin/Staff/Client) | `apps/*/__main__.py` | Login fonctionnel |\n| 5 | Tester mobile (<700px) | Navigateur | Formulaire seul affiché |",
    "auth-locale": "| 1 | Configurer SECRET_KEY dans config.ini | `config.ini` | Clé de 32+ caractères |\n| 2 | Implémenter hash_password + create_token | `auth.py` | bcrypt + JWT fonctionnels |\n| 3 | Implémenter login(email, password) | `auth.py` | Retourne access_token |\n| 4 | Implémenter generate_activation | `auth.py` | Code hex + QR URL générés |\n| 5 | Implémenter activate_device | `auth.py` | Device enregistré en DB |\n| 6 | Implémenter create_first_admin | `auth.py` | Établissement + admin créés |\n| 7 | Tester : login valide, mdp erroné, code expiré | `pytest tests/test_auth.py` | 16 tests verts |",
    "catalogue-3panels": "| 1 | Implémenter _fetch_categories + _fetch_produits | `apps/admin/__main__.py` | Données chargées |\n| 2 | Construire panneau gauche (catégories) | `apps/admin/__main__.py` | Liste cliquable |\n| 3 | Construire panneau central (produits filtrés) | `apps/admin/__main__.py` | Filtrage par catégorie |\n| 4 | Construire panneau droit (détail) | `apps/admin/__main__.py` | Détail produit affiché |\n| 5 | Ajouter dialog ajout/modif produit | `apps/admin/__main__.py` | CRUD fonctionnel |\n| 6 | Ajouter dialog ajout catégorie | `apps/admin/__main__.py` | Catégories gérables |",
    "crud-m3": "| 1 | Implémenter soft_delete (table, id, uid) | Module DB | DELETE logique |\n| 2 | Implémenter insert_record avec UUID + audit | Module DB | INSERT avec traçabilité |\n| 3 | Implémenter update_record avec optimistic lock | Module DB | UPDATE avec détection conflit |\n| 4 | Implémenter fetch_all avec deleted_at IS NULL | Module DB | Lecture filtrée |\n| 5 | Créer dialogs M3 (créer, modifier, confirmer) | UI | Interfaces standardisées |\n| 6 | Tester : conflit version → ValueError | pytest | Exception levée correctement |",
    "kds-kanban": "| 1 | Implémenter _lignes(cmd_id) avec jointure | `apps/staff/__main__.py` | Plats par commande |\n| 2 | Construire kanban 3 colonnes | `apps/staff/__main__.py` | Layout kanban |\n| 3 | Implémenter _ch_kds(cmd_id, statut) | `apps/staff/__main__.py` | Avancement DB |\n| 4 | Ajouter badges compteurs + couleurs | `apps/staff/__main__.py` | Visuel colonnes |\n| 5 | Ajouter bouton refresh | `apps/staff/__main__.py` | Rechargement manuel |\n| 6 | Ajouter polling 10s (optionnel) | `apps/staff/__main__.py` | Auto-refresh |",
    "graphity": "| 1 | Parser Python : class, def, import | `graphity.py` | Données extraites |\n| 2 | Parser SQL : CREATE TABLE, FK | `graphity.py` | Tables listées |\n| 3 | Générer index.md (hub) | `graphity.py` | Navigation centrale |\n| 4 | Générer notes par classe | `graphity.py` | Une note par classe |\n| 5 | Générer notes par table DB | `graphity.py` | Une note par table |\n| 6 | Générer guides utilisateur | `graphity.py` | Aide-Admin/Staff/Client.md |\n| 7 | Lancer `python graphity.py` | Terminal | Vault Obsidian prêt |",
    "wordpress-theme": "| 1 | Créer style.css avec tokens M3 | `wp-content/themes/artizboard/` | CSS chargé |\n| 2 | Créer PHP : header, footer, functions, index | `wp-content/themes/artizboard/` | Structure WP |\n| 3 | Créer JS : config, api, cart, app | `wp-content/themes/artizboard/assets/js/` | Logique client |\n| 4 | Injecter clés Supabase dans config.js | `deploy_site.py` | Connexion Supabase |\n| 5 | Uploader via FTP sur Hostinger | `deploy_site.py` | Fichiers en ligne |\n| 6 | Activer thème + créer pages WordPress | Admin WP | Site en ligne |\n| 7 | Vérifier : cart, menu, à propos, contact | Navigateur | Toutes les sections OK |",
    "design-system": "| 1 | Importer ds + appliquer à la page | `main()` | Thème M3 actif |\n| 2 | Utiliser ds.p.* pour toutes les couleurs | Partout | 0 hardcoding |\n| 3 | Utiliser ds.space_* pour les espacements | Partout | Fibonacci respecté |\n| 4 | Utiliser ds.textstyle() pour la typo | Partout | Échelle M3 |\n| 5 | Utiliser ds.SHAPE_* pour les bordures | Partout | Radius cohérents |\n| 6 | Vérifier checklist (10 règles) | Revue de code | Conformité M3 |",
    "artizboard-m3": "| 1 | ds.apply(page) dans main() | Toute app | Thème appliqué |\n| 2 | Respecter Fibonacci pour les espacements | Partout | Tokens cohérents |\n| 3 | Utiliser golden_split pour layouts 2 colonnes | Partout | Proportions φ |\n| 4 | Fenêtre login : fixe, centrée, φ | Login | 1100×680 |\n| 5 | Fenêtre dashboard : maximisée | Dashboard | Plein écran |\n| 6 | Vérifier anti-patterns (❌→✅) | Revue de code | 0 erreurs |",
    "flet-wrapper": "| 1 | Remplacer ft.ElevatedButton → ft.Button | `ftw.py` | Plus de dépréciation |\n| 2 | Utiliser alignment via ft.alignment.Alignment(x,y) | Partout | Pas de tuples |\n| 3 | Utiliser border_radius via ds.SHAPE_XS.radius | Partout | Pas d'entiers bruts |\n| 4 | Protéger les .update() avec try/except | Partout | Pas de RuntimeError |\n| 5 | Centrer fenêtre via tkinter | Login | Fenêtre centrée |\n| 6 | Lancer en web : ft.app(target=main) | main() | Mode web |",
    "documenter-skill": "| 1 | Créer dossier skill | Terminal | `open-design/skills/<nom>/` |\n| 2 | Rédiger sections 0→5 dans SKILL.md | Éditeur | Document complet |\n| 3 | Générer .docx + Obsidian | `generate_skill_outputs.py` | 3 formats |\n| 4 | Valider checklist | Lecture | Tous les ✓ |",
}

for skill_dir in sorted(SKILLS_DIR.iterdir()):
    if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
        continue

    name = skill_dir.name
    md_path = skill_dir / "SKILL.md"
    content = md_path.read_text(encoding="utf-8")

    # Skip if already has Contexte
    if "## 0. Contexte" in content:
        print(f"  SKIP {name}: Contexte already present")
        continue

    # Add Contexte after title line
    context_text = CONTEXTS.get(name, f"**Projet** : ArtizBoard\n**Module** : `{name}`\n**Utilisateurs** : Tous\n**Dépendances** : Aucune\n**Prérequis** : Aucun")
    content = content.replace(
        f"# Skill:",
        f"# Skill:",
        1  # Only first occurrence
    )
    # Insert after first heading line
    lines = content.split("\n")
    new_lines = []
    inserted_context = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        if not inserted_context and line.startswith("# Skill:") and i+1 < len(lines) and lines[i+1].strip() == "":
            new_lines.append("")
            new_lines.append("## 0. Contexte")
            new_lines.append("")
            for ctx_line in context_text.split("\n"):
                new_lines.append(ctx_line)
            new_lines.append("")
            inserted_context = True

    content = "\n".join(new_lines)

    # Add Step by Step before Checklist section
    steps_text = STEPS.get(name, "| 1 | Lire la doc | `SKILL.md` | Compréhension |\n| 2 | Implémenter | Code | Fonctionnel |")
    checklist_marker = "## Checklist"
    if checklist_marker in content:
        step_block = f"## 5. Step by Step — Implementation\n\n| Ordre | Action | Fichier | Resultat |\n|---|---|---|---|\n{steps_text}\n\n"
        content = content.replace(checklist_marker, step_block + checklist_marker)

    md_path.write_text(content, encoding="utf-8")
    print(f"  OK {name}")

print("\nDone")
