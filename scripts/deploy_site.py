"""ArtizBoard — Deployer le site WordPress sur Hostinger

Usage: python deploy_site.py
"""
import os, sys, zipfile, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ArtizBoardCommon.config_loader import get_supabase_config

import configparser
CONFIG = configparser.ConfigParser(os.environ)
CONFIG.read(str(Path(__file__).parent / "ArtizBoardCommon" / "config.ini"), encoding="utf-8")

supabase_url, supabase_anon, _ = get_supabase_config()
FTP_HOST = CONFIG.get("hostinger", "ftp_host", fallback="")
FTP_PORT = CONFIG.getint("hostinger", "ftp_port", fallback=21)
FTP_USER = CONFIG.get("hostinger", "ftp_user", fallback="")
FTP_PASS = CONFIG.get("hostinger", "ftp_password", fallback="")
WP_URL = CONFIG.get("hostinger", "wordpress_url", fallback="").rstrip("/")
WP_USER = CONFIG.get("hostinger", "wordpress_user", fallback="")
WP_PASS = CONFIG.get("hostinger", "wordpress_app_password", fallback="")

THEME_DIR = Path(__file__).parent / "wp-content" / "themes" / "artizboard"
BUILD_DIR = Path(__file__).parent / "build" / "theme_upload"
BUILD_DIR.mkdir(parents=True, exist_ok=True)

def inject_keys():
    """Injecte les cles Supabase dans config.js"""
    cf = THEME_DIR / "assets" / "js" / "config.js"
    content = cf.read_text(encoding="utf-8")
    content = content.replace("var SUPABASE_URL = 'https://xxxxxxxxxxxx.supabase.co';",
                              f"var SUPABASE_URL = '{supabase_url}';")
    content = content.replace("var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';",
                              f"var SUPABASE_ANON_KEY = '{supabase_anon}';")
    cf.write_text(content, encoding="utf-8")
    print("[deploy] Cles Supabase injectees")

def upload_ftp():
    """Upload recursif du theme via FTP"""
    if not FTP_HOST:
        print("[deploy] FTP non configure")
        return False

    from ftplib import FTP
    ftp = FTP()
    ftp.connect(FTP_HOST, FTP_PORT, timeout=30)
    ftp.login(FTP_USER, FTP_PASS)
    print(f"[deploy] FTP connecte, root: {ftp.pwd()}")

    base = Path("/")
    try:
        ftp.cwd("public_html")
        base = Path("/public_html")
    except:
        for domain_dir in ["domains", "aristodetoonasi.com", "public_html"]:
            try:
                ftp.cwd(domain_dir)
                base = base / domain_dir
            except:
                pass
    print(f"[deploy] Public HTML: {base}")

    # wp-content/themes/
    wp_base = str(base / "wp-content" / "themes")
    for part in ["wp-content", "themes"]:
        try:
            ftp.cwd(part)
        except:
            ftp.mkd(part)
            ftp.cwd(part)

    # Supprimer ancien theme si existe
    try:
        ftp.cwd("artizboard")
        _rmtree(ftp)
        ftp.cwd("..")
    except:
        pass

    ftp.mkd("artizboard")
    ftp.cwd("artizboard")
    theme_base = ftp.pwd()
    print(f"[deploy] Upload vers {theme_base}")

    local_root = THEME_DIR.parent.parent  # wp-content/
    count = 0
    for fp in sorted(THEME_DIR.rglob("*")):
        if not fp.is_file() or fp.name.startswith("."):
            continue
        rel = fp.relative_to(local_root)  # themes/artizboard/...
        parts = list(rel.parts)

        ftp.cwd(theme_base)
        for d in parts[:-1]:
            try:
                ftp.cwd(d)
            except:
                ftp.mkd(d)
                ftp.cwd(d)

        with open(fp, "rb") as fh:
            ftp.storbinary(f"STOR {parts[-1]}", fh)
        count += 1

    print(f"[deploy] {count} fichiers uploades")
    ftp.quit()
    return True

def _rmtree(ftp):
    items = []
    try:
        ftp.retrlines("LIST", items.append)
    except:
        items = []
    for item in items:
        parts = item.split()
        if len(parts) < 4:
            continue
        name = parts[-1]
        if parts[0].startswith("d"):
            try:
                ftp.cwd(name)
                _rmtree(ftp)
                ftp.cwd("..")
                ftp.rmd(name)
            except:
                pass
        else:
            try:
                ftp.delete(name)
            except:
                pass

def create_pages():
    """Cree les pages WordPress"""
    if not WP_URL or not WP_USER or not WP_PASS:
        print("[deploy] WordPress API non configuree - pages a creer manuellement")
        return

    import base64
    auth = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

    pages = [
        ("carte", "Notre Carte", "template-carte.php"),
        ("apropos", "A Propos", "template-apropos.php"),
        ("contact", "Nous Contacter", "template-contact.php"),
    ]

    for slug, title, template in pages:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{WP_URL}/wp-json/wp/v2/pages?slug={slug}", headers=headers)
            resp = urllib.request.urlopen(req)
            existing = json.loads(resp.read())

            if existing:
                pid = existing[0]["id"]
                req = urllib.request.Request(
                    f"{WP_URL}/wp-json/wp/v2/pages/{pid}",
                    data=json.dumps({"template": template}).encode(),
                    headers=headers, method="POST")
                urllib.request.urlopen(req)
                print(f"[deploy] OK page '{title}' mise a jour")
            else:
                req = urllib.request.Request(
                    f"{WP_URL}/wp-json/wp/v2/pages",
                    data=json.dumps({"slug": slug, "title": title,
                                     "template": template, "status": "publish"}).encode(),
                    headers=headers)
                urllib.request.urlopen(req)
                print(f"[deploy] OK page '{title}' creee")
        except Exception as e:
            print(f"[deploy] ERR page '{title}': {e}")

def main():
    print("=" * 50)
    print("ArtizBoard - Deploiement WordPress")
    print("=" * 50)

    inject_keys()

    ok = upload_ftp()
    if ok:
        print("=" * 50)
        print("OK Deploiement termine")
    else:
        zip_path = BUILD_DIR / "artizboard.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for fp in THEME_DIR.rglob("*"):
                if fp.is_file():
                    zf.write(fp, fp.relative_to(THEME_DIR.parent.parent))
        print(f"ZIP: {zip_path} ({zip_path.stat().st_size:,} octets)")

    print()
    create_pages()

if __name__ == "__main__":
    main()
