"""ArtizBoard — Pipeline de livraison

Usage: python livrer.py

1. Verifie les tests (171 tests)
2. Genere la documentation (graphity + skills)
3. Build les apps (.exe)
4. Pack tout dans un ZIP livrable
5. Genere README-LIVRAISON.md
"""
import sys, os, subprocess, shutil, zipfile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
DIST = ROOT / "dist" / f"ArtizBoard-{datetime.now().strftime('%Y%m%d')}"
DIST.mkdir(parents=True, exist_ok=True)

def run(cmd: str, label: str) -> bool:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True, text=True)
    if result.stdout: print(result.stdout[-500:])
    if result.returncode != 0:
        print(f"  [ERREUR] {label}")
        if result.stderr: print(result.stderr[-300:])
        return False
    print(f"  [OK] {label}")
    return True

def step(label: str):
    print(f"\n  >> {label}")

def main():
    print("=" * 60)
    print("  ArtizBoard — Pipeline de Livraison")
    print("=" * 60)

    # ── 0. Compilation check ──
    step("0/6 Verification compilation...")
    app_files = [
        "apps/admin/__main__.py", "apps/staff/__main__.py", "apps/client/__main__.py",
        "apps/common/auth.py", "apps/common/login.py"
    ]
    import py_compile
    for f in app_files:
        try:
            py_compile.compile(str(ROOT / f), doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  ERREUR COMPILATION: {f}")
            print(f"  {e}")
            sys.exit(1)
    print(f"     {len(app_files)} fichiers OK")

    # ── 1. Tests ──
    step("1/6 Lancement des tests...")
    result = subprocess.run("python -m pytest tests/ -v --tb=short", shell=True, cwd=str(ROOT),
                           capture_output=True, text=True)
    # Afficher le resume
    for line in result.stdout.split("\n"):
        if "passed" in line or "failed" in line or "ERROR" in line:
            print(f"     {line.strip()}")
    if result.returncode != 0:
        print("\n  ATTENTION: Certains tests ne passent pas.")
        print(result.stdout[-1000:])
        if input("  Continuer quand meme ? (o/n) ").lower() != 'o':
            sys.exit(1)

    # ── 2. Documentation ──
    step("2/6 Generation documentation...")
    if not run("python graphity.py", "Graphity (graphe de code)"): pass
    if not run("python generate_skill_outputs.py --all", "Skills × 3 formats"): pass

    # ── 3. ZIP WordPress ──
    step("3/6 Creation du ZIP WordPress...")
    if not run("python build/zip_theme.py", "ZIP WordPress"): pass

    # ── 4. Copier les fichiers livrables ──
    step("4/6 Assemblage du dossier de livraison...")

    # WordPress theme
    shutil.copy(ROOT / "build/theme_upload/artizboard.zip", DIST / "theme-wordpress.zip")

    # Build scripts
    for bat in ["build_admin_desktop.bat", "build_staff_desktop.bat", "build_client_desktop.bat",
                 "build_staff_apk.bat", "build_all.bat", "build_all_and_zip.bat"]:
        src = ROOT / "build" / bat
        if src.exists():
            shutil.copy(src, DIST / bat)

    # Documentation
    doc_dir = DIST / "documentation"
    doc_dir.mkdir(exist_ok=True)
    if (ROOT / "open-design/graph").exists():
        shutil.copytree(ROOT / "open-design/graph", doc_dir / "graphe-code", dirs_exist_ok=True)
    if (ROOT / "open-design/skills").exists():
        shutil.copytree(ROOT / "open-design/skills", doc_dir / "skills", dirs_exist_ok=True)
    if (ROOT / "open-design/DESIGN.md").exists():
        shutil.copy(ROOT / "open-design/DESIGN.md", doc_dir / "DESIGN.md")

    # Source SQL
    db_dir = DIST / "base-de-donnees"
    db_dir.mkdir(exist_ok=True)
    for sql in (ROOT / "db").glob("*.sql"):
        shutil.copy(sql, db_dir / sql.name)

    # LICENSE
    if (ROOT / "LICENSE").exists():
        shutil.copy(ROOT / "LICENSE", DIST / "LICENSE")

    print(f"     Dossier: {DIST}")

    # ── 5. README livraison ──
    step("5/6 Generation README-LIVRAISON.md...")
    readme = f"""# ArtizBoard — Livraison v{datetime.now().strftime('%Y%m%d')}

## Contenu du dossier

| Dossier/Fichier | Contenu |
|---|---|
| `base-de-donnees/` | Scripts SQL pour PostgreSQL local |
| `documentation/` | Graphe de code + 13 skills (MD, DOCX, Obsidian) |
| `theme-wordpress.zip` | Thème WordPress a deployer sur Hostinger |
| `*.bat` | Scripts de compilation (.exe, .apk) |
| `LICENSE` | Licence MIT |

## Installation

### Prérequis
- Python 3.10+ avec pip
- PostgreSQL 15+
- Compte Supabase (gratuit)

### 1. Base de données locale
```bash
createdb ArtizBoard
psql -d ArtizBoard -f base-de-donnees/init_pg_local.sql
```

### 2. Supabase Cloud
- Creer un projet sur https://supabase.com
- Executer `base-de-donnees/init_supabase.sql` dans le SQL Editor
- Configurer les cles dans `ArtizBoardCommon/config.ini`

### 3. Installer les dependances
```bash
pip install -r requirements.txt   # ou pip install flet psycopg2 bcrypt pillow supabase
```

### 4. Lancer les apps
```bash
python seed_db.py          # Donnees de demo
python -m apps.admin       # Interface Admin (PC)
python -m apps.staff       # App Staff (mobile/web)
python -m apps.client      # Portail Client (web)
python sync_service.py     # Synchronisation Supabase
```

### 5. Compiler en .exe ou .apk
```bash
build_admin_desktop.bat    # → ArtizBoard Admin.exe
build_staff_desktop.bat    # → ArtizBoard Staff.exe
build_staff_apk.bat        # → ArtizBoard Staff.apk
```

### 6. Site WordPress
- Uploader `theme-wordpress.zip` dans `wp-content/themes/` sur Hostinger
- Extraire → Activer le theme "ArtizBoard"
- Creer 3 pages : /carte, /apropos, /contact
- Les donnees viennent de Supabase automatiquement

## Support
- Documentation complete dans `documentation/`
- Ouvrir `documentation/graphe-code/` dans Obsidian pour naviguer
- Licence MIT — voir `LICENSE`

---
Genere le {datetime.now().strftime('%d/%m/%Y')} par `livrer.py`
"""
    (DIST / "README-LIVRAISON.md").write_text(readme, encoding="utf-8")
    print(f"     README-LIVRAISON.md genere")

    # ── 6. ZIP final ──
    step("6/6 Creation du ZIP final...")
    zip_path = ROOT / "dist" / f"ArtizBoard-v{datetime.now().strftime('%Y%m%d')}.zip"
    with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        for fp in DIST.rglob("*"):
            if fp.is_file():
                zf.write(fp, fp.relative_to(DIST))
    size_mb = zip_path.stat().st_size / (1024*1024)
    print(f"\n{'='*60}")
    print(f"  LIVRAISON TERMINEE")
    print(f"{'='*60}")
    print(f"  ZIP : {zip_path}")
    print(f"  Taille : {size_mb:.1f} Mo")
    print(f"  Contenu :")
    for item in sorted(DIST.iterdir()):
        if item.is_dir():
            count = len(list(item.rglob("*")))
            print(f"    {item.name}/ ({count} fichiers)")
        else:
            print(f"    {item.name}")
    print(f"\n  Pour installer : decompresser le ZIP, suivre README-LIVRAISON.md")

if __name__ == "__main__":
    main()
