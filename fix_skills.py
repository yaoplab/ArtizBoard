"""Fix the 5 original skills to add ## 1. Fonction Principale section."""
from pathlib import Path
import re

SKILLS_DIR = Path(__file__).parent / "open-design" / "skills"

FIXES = {
    'artizboard-m3': (
        "## 1. Fonction Principale\n\n"
        "### Type : Systeme Ferme\n\n"
        "**Entrée** : Composant Flet non stylé\n"
        "**Sortie** : Composant M3 conforme (couleurs, espacements, typo, shapes)\n"
        "**Traitement** : Appliquer ds.p.*, ds.space_*, ds.textstyle(), ds.SHAPE_*\n"
    ),
    'design-system': (
        "## 1. Fonction Principale\n\n"
        "### Type : Systeme Ferme\n\n"
        "**Entrée** : Page Flet (ft.Page)\n"
        "**Sortie** : Page avec thème M3 complet appliqué\n"
        "**Traitement** : ds.apply(page) → injection couleurs, polices, shapes via ft.Theme\n"
    ),
    'flet-wrapper': (
        "## 1. Fonction Principale\n\n"
        "### Type : Systeme Ferme\n\n"
        "**Entrée** : Composant Flet avec ancienne API (< 0.86)\n"
        "**Sortie** : Composant compatible Flet 0.86+\n"
        "**Traitement** : Remplacer API dépréciées (ElevatedButton → Button, tuples → Alignment, etc.)\n"
    ),
    'wordpress-theme': (
        "## 1. Fonction Principale\n\n"
        "### Type : Systeme Ferme\n\n"
        "**Entrée** : Clés Supabase (anon_key) + thème PHP/JS\n"
        "**Sortie** : Site WordPress déployé sur Hostinger\n"
        "**Traitement** : PHP templates → JS Supabase SDK → rendu → FTP deploy\n"
    ),
}

for skill_dir in sorted(SKILLS_DIR.iterdir()):
    name = skill_dir.name
    if name not in FIXES:
        continue
    md = skill_dir / "SKILL.md"
    content = md.read_text(encoding="utf-8")

    # Skip if already fixed
    if "## 1. Fonction Principale" in content:
        print(f"  SKIP {name}: already has section 1")
        continue

    # Insert after "## 0. Contexte" block
    new_content = re.sub(
        r"(## 0\. Contexte\n.*?\n\n)",
        r"\1" + FIXES[name] + "\n",
        content, count=1, flags=re.DOTALL
    )
    md.write_text(new_content, encoding="utf-8")
    print(f"  FIXED {name}")

print("Done")
