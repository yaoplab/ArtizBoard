"""Audit de securite automatique pour ArtizBoard.

Usage: python audit_securite.py
"""
import re, sys, subprocess, json
from pathlib import Path

ROOT = Path(__file__).parent

class SecurityAudit:
    def __init__(self):
        self.findings = []
        self.passed = []

    def add(self, level, section, msg, filepath="", fix=""):
        self.findings.append({"level": level, "section": section, "msg": msg, "file": filepath, "fix": fix})

    def ok(self, section, msg):
        self.passed.append({"section": section, "msg": msg})

    def audit_sql_injection(self):
        s = "SQL Injection"
        for py in ROOT.rglob("*.py"):
            if '.venv' in str(py): continue
            try:
                c = py.read_text(encoding="utf-8")
                rel = str(py.relative_to(ROOT))
                if re.search(r'execute\(f"', c) or re.search(r"execute\(f'", c):
                    self.add(5, s, "f-string dans requete SQL", rel, "Utiliser %s + tuple de parametres")
                if re.search(r'execute\(".*%[sd]', c):
                    self.add(4, s, "Formatage % dans requete SQL", rel)
                if re.search(r'execute\(.*\.format\(', c):
                    self.add(4, s, ".format() dans requete SQL", rel)
                if re.search(r'execute\(".*" \+', c):
                    self.add(4, s, "Concatenation + dans requete SQL", rel)
            except: pass
        self.ok(s, "Scan SQL injection termine")

    def audit_secrets(self):
        s = "Secrets"
        for py in ROOT.rglob("*.py"):
            if '.venv' in str(py): continue
            try:
                c = py.read_text(encoding="utf-8")
                rel = str(py.relative_to(ROOT))
                for pat, lvl, msg in [
                    (r'password\s*=\s*["\'][^"\'$]{3,}', 4, "Mot de passe en dur"),
                    (r'secret\s*=\s*["\'][^"\'$]{10,}', 4, "Secret en dur"),
                    (r'api_key\s*=\s*["\'][^"\'$]{10,}', 4, "Cle API en dur"),
                ]:
                    if re.search(pat, c):
                        self.add(lvl, s, msg, rel, "Deplacer dans config.ini")
            except: pass

        config = ROOT / "ArtizBoardCommon" / "config.ini"
        if config.exists():
            ct = config.read_text()
            if "change-me-in-production" in ct:
                self.add(5, s, "SECRET_KEY = 'change-me-in-production' (valeur par defaut)", "config.ini", "Generer une cle de 32+ caracteres aleatoires")
            m = re.search(r'jwt_secret_key\s*=\s*(.+)', ct)
            if m and len(m.group(1).strip()) < 32:
                self.add(4, s, "SECRET_KEY < 32 caracteres", "config.ini")
        self.ok(s, "Scan secrets termine")

    def audit_auth(self):
        s = "Authentification"
        auth_py = ROOT / "apps" / "common" / "auth.py"
        if auth_py.exists():
            c = auth_py.read_text()
            if "gensalt()" in c and "rounds" not in c:
                self.add(2, s, "bcrypt.gensalt() sans rounds explicite (defaut=12, OK)", "auth.py")
            m = re.search(r'ACTIVATION_EXPIRE_MINUTES\s*=\s*(\d+)', c)
            if m and int(m.group(1)) > 30:
                self.add(4, s, f"Code activation expire en {m.group(1)} min (> 30 recommande)", "auth.py")
            if "JWT_ALGORITHM" in c and "HS256" not in c:
                self.add(4, s, "JWT n'utilise pas HS256", "auth.py")
            if "JWT_EXPIRY_MINUTES" in c:
                m = re.search(r'JWT_EXPIRY_MINUTES\s*=\s*(\d+)', c)
                if m and int(m.group(1)) > 60:
                    self.add(4, s, f"JWT expire en {m.group(1)} min (> 60 recommande)", "auth.py")
        self.ok(s, "Scan auth termine")

    def audit_database(self):
        s = "Base de donnees"
        init_sql = ROOT / "db" / "init_pg_local.sql"
        if init_sql.exists():
            c = init_sql.read_text()
            if "ON DELETE CASCADE" in c:
                self.add(5, s, "ON DELETE CASCADE detecte", "init_pg_local.sql", "Remplacer par soft delete")
            if "deleted_at" not in c:
                self.add(5, s, "Pas de colonne deleted_at (soft delete manquant)", "init_pg_local.sql")
            if "version INTEGER DEFAULT 1" not in c:
                self.add(5, s, "Pas de colonne version (optimistic locking)", "init_pg_local.sql")

        sb_sql = ROOT / "db" / "init_supabase.sql"
        if sb_sql.exists():
            c = sb_sql.read_text()
            tables = re.findall(r"CREATE TABLE (\w+)", c)
            rls_tables = re.findall(r"ALTER TABLE (\w+) ENABLE ROW LEVEL SECURITY", c)
            for t in tables:
                if t not in rls_tables and t != "schema_version":
                    self.add(3, s, f"Table {t} sans RLS active", "init_supabase.sql")

        pgb = ROOT / "db" / "pgbouncer.ini"
        if pgb.exists():
            c = pgb.read_text()
            if "pool_mode = transaction" not in c:
                self.add(4, s, "PgBouncer pas en mode transaction", "pgbouncer.ini")
        self.ok(s, "Scan DB termine")

    def audit_inputs(self):
        s = "Validation Entrees"
        for py in ROOT.rglob("*.py"):
            if '.venv' in str(py): continue
            try:
                c = py.read_text(encoding="utf-8")
                if re.search(r'\beval\(', c):
                    self.add(5, s, "eval() detecte", str(py.relative_to(ROOT)), "Supprimer eval()")
                if re.search(r'\bexec\(', c):
                    self.add(5, s, "exec() detecte", str(py.relative_to(ROOT)), "Supprimer exec()")
            except: pass
        self.ok(s, "Scan inputs termine")

    def audit_dependencies(self):
        s = "Dependances"
        try:
            r = subprocess.run(["pip", "list", "--outdated", "--format=json"], capture_output=True, text=True, timeout=20)
            if r.returncode == 0:
                outdated = json.loads(r.stdout)
                if len(outdated) > 20:
                    self.add(2, s, f"{len(outdated)} packages obsoletes")
                for pkg in outdated[:10]:
                    self.add(2, s, f"{pkg['name']} {pkg['version']} -> {pkg['latest_version']}")
        except: pass
        self.ok(s, "Scan dependances termine")

    def audit_frontend(self):
        s = "Frontend/JS"
        for js in ROOT.rglob("*.js"):
            if '.venv' in str(js): continue
            try:
                c = js.read_text(encoding="utf-8")
                rel = str(js.relative_to(ROOT))
                if re.search(r'\beval\(', c):
                    self.add(5, s, "eval() dans JS", rel)
                if re.search(r'innerHTML\s*=', c):
                    self.add(4, s, "innerHTML sans echappement, risque XSS", rel)
            except: pass

        config_js = ROOT / "wp-content" / "themes" / "artizboard" / "assets" / "js" / "config.js"
        if config_js.exists():
            c = config_js.read_text(encoding="utf-8")
            if "service_role" in c.lower() or "secret" in c.lower():
                self.add(5, s, "Cle service_role/secret exposee dans config.js", "config.js", "Utiliser uniquement anon_key en frontend")
        self.ok(s, "Scan frontend termine")

    def audit_wordpress(self):
        s = "WordPress"
        self.add(2, s, "Verifier: WordPress + plugins a jour", "wp-admin", "Dashboard > Mises a jour")
        self.add(2, s, "Verifier: REST API non expose sans auth si inutile", "", "Bloquer /wp-json/wp/v2/users si non requis")
        self.add(2, s, "Verifier: xmlrpc.php desactive", "", "Ajouter au .htaccess: Redirect 403 /xmlrpc.php")
        self.ok(s, "Recommandations WordPress listees")

    def run(self):
        self.audit_sql_injection()
        self.audit_secrets()
        self.audit_auth()
        self.audit_database()
        self.audit_inputs()
        self.audit_dependencies()
        self.audit_frontend()
        self.audit_wordpress()

        self.findings.sort(key=lambda x: -x['level'])
        return self

    def report(self):
        self.run()
        levels = {5: "CRITIQUE", 4: "ELEVE", 3: "MOYEN", 2: "FAIBLE", 1: "INFO"}
        print("=" * 60)
        print("  AUDIT DE SECURITE — ArtizBoard")
        print("=" * 60)
        crit = sum(1 for f in self.findings if f['level'] >= 5)
        high = sum(1 for f in self.findings if f['level'] == 4)
        print(f"  Vulns : {len(self.findings)} ({crit} critiques, {high} elevees)")
        print(f"  OK    : {len(self.passed)} controles passes")
        print("=" * 60)

        for f in self.findings:
            print(f"\n  [{levels.get(f['level'], f['level'])}] {f['section']}")
            print(f"  {f['msg']}")
            if f['file']: print(f"  -> {f['file']}")
            if f['fix']: print(f"  Fix: {f['fix']}")

        print(f"\n{'='*60}")
        if crit == 0 and high == 0:
            print("  [OK] Aucune vulnerabilite critique ou elevee.")
        else:
            print(f"  [ACTION] {crit + high} vulnerabilites a corriger prioritairement.")
        print("=" * 60)

if __name__ == "__main__":
    SecurityAudit().report()
