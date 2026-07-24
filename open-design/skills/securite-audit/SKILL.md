# Skill: Sécurité — Audit Complet

## 0. Contexte

**Projet** : ArtizBoard (local-first, PostgreSQL + Supabase + Flet + WordPress)
**Rôle** : Auditer la sécurité des apps, de la base, et des flux réseau
**Dépendances** : Tous les modules
**Prérequis** : Code accessible, DB locale, Supabase connecté

## 1. Fonction Principale

### Type : Système Ouvert

```
ENTRÉE                               →  TRAITEMENT                              →  SORTIE
Code source (Python, JS, SQL, PHP)     8 audits thématiques                     ├─ Rapport de vulnérabilités
Base de données (PostgreSQL)           Scan statique + analyse de config         ├─ Niveau de risque (1-5)
Config (config.ini, Supabase)          Vérification des bonnes pratiques         └─ Correctifs recommandés
```

## 2. Contraintes Fonctionnelles

### Tableau global — Niveaux de risque

| Niveau | Nom | Action |
|---|---|---|
| 🔴 5 | Critique | Bloquant — corriger immédiatement |
| 🟠 4 | Élevé | Prioritaire — corriger avant mise en prod |
| 🟡 3 | Moyen | Recommandé — corriger dans la semaine |
| 🔵 2 | Faible | Souhaitable — bonne pratique |
| ⚪ 1 | Info | Information — pas d'action requise |

### Sous-système A — Audit SQL Injection

**Fonction** : Vérifier que toutes les requêtes SQL sont paramétrées

| # | Contrainte |
|---|---|
| A1 | Toute requête doit utiliser `%s` avec un tuple de paramètres |
| A2 | JAMAIS de f-string ou `+` dans une requête SQL |
| A3 | JAMAIS de `format()` ou `%` dans une requête SQL |
| A4 | Les noms de tables dynamiques doivent être validés contre une whitelist |

### Sous-système B — Audit Secrets & Config

**Fonction** : Détecter les secrets en dur dans le code

| # | Contrainte |
|---|---|
| B1 | Aucune clé API, mot de passe, token en dur dans le code source |
| B2 | `SECRET_KEY` doit faire ≥ 32 caractères |
| B3 | `SECRET_KEY` ne doit pas être la valeur par défaut (`change-me-in-production`) |
| B4 | Le fichier `config.ini` ne doit pas être commité (dans `.gitignore`) |
| B5 | Les clés Supabase dans `config.js` ne sont exposées que via `anon_key` |

### Sous-système C — Audit Authentification

**Fonction** : Vérifier la robustesse du système d'auth

| # | Contrainte |
|---|---|
| C1 | bcrypt utilisé avec cost factor ≥ 12 (vérifier `gensalt()`) |
| C2 | JWT signé avec algorithme HS256 minimum |
| C3 | JWT expire dans ≤ 60 minutes |
| C4 | Codes d'activation : 8+ caractères hex, 3 tentatives max, 5-30 min d'expiration |
| C5 | Pas de stockage de mot de passe en clair |
| C6 | Refresh token stocké hashé ou à durée limitée |

### Sous-système D — Audit Base de Données

**Fonction** : Vérifier la configuration PostgreSQL

| # | Contrainte |
|---|---|
| D1 | Pas de connexion en `trust` — toujours `md5` ou `scram-sha-256` |
| D2 | PgBouncer en mode `transaction` (pas `session`) |
| D3 | `max_client_conn` limité à 150 |
| D4 | Soft delete sur toutes les tables sensibles |
| D5 | Optimistic locking sur toutes les tables modifiables |
| D6 | Supabase RLS activé sur toutes les tables publiques |
| D7 | Pas de `ON DELETE CASCADE` destructif |

### Sous-système E — Audit Input/Output

**Fonction** : Vérifier la validation des entrées

| # | Contrainte |
|---|---|
| E1 | Toute entrée utilisateur est validée avant traitement |
| E2 | Les champs numériques sont castés avec try/except |
| E3 | Injection HTML/XSS : les entrées HTML sont échappées |
| E4 | Upload de fichier : type MIME vérifié, taille limitée |
| E5 | Pas d'exécution de code dynamique (`eval`, `exec`) |

### Sous-système F — Audit Dépendances

**Fonction** : Vérifier les vulnérabilités connues

| # | Contrainte |
|---|---|
| F1 | `pip list --outdated` — pas de dépendance avec CVE critique |
| F2 | Python ≥ 3.10 (fin de vie 3.9) |
| F3 | Flet ≥ 0.86 (dernière stable) |
| F4 | psycopg2 ≥ 2.9 (pas psycopg2-binary en prod) |
| F5 | Pas de dépendance non maintenue depuis > 1 an |

### Sous-système G — Audit Frontend/JS

**Fonction** : Vérifier la sécurité côté client

| # | Contrainte |
|---|---|
| G1 | Pas de `eval()` ou `innerHTML` non sécurisé |
| G2 | Supabase anon_key utilisée pour les lectures (pas service_role) |
| G3 | localStorage : pas de données sensibles (JWT refresh ok, pas de mdp) |
| G4 | CORS : les appels API sont limités au domaine Supabase |
| G5 | Pas de clé privée exposée dans le JS client |

### Sous-système H — Audit WordPress

**Fonction** : Vérifier la sécurité du thème

| # | Contrainte |
|---|---|
| H1 | `wp-config.php` n'est pas accessible en lecture publique |
| H2 | Pas de `admin` comme nom d'utilisateur WordPress |
| H3 | REST API désactivé pour les non-authentifiés si non nécessaire |
| H4 | Les uploads ne permettent pas l'exécution PHP |
| H5 | `xmlrpc.php` désactivé ou protégé |
| H6 | WordPress et plugins à jour |

## 3. Code — Script d'audit

```python
# audit_securite.py — Scan automatique de sécurité
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent

class SecurityAudit:
    def __init__(self):
        self.findings = []
        self.passed = []
    
    def add(self, level: int, section: str, message: str, file: str = "", fix: str = ""):
        self.findings.append({
            "level": level, "section": section, "message": message, "file": file, "fix": fix
        })
    
    def pass_(self, section: str, message: str):
        self.passed.append(f"[OK] {section}: {message}")
    
    # A. SQL Injection
    def audit_sql_injection(self):
        section = "SQL Injection"
        patterns = [
            (r'execute\(f"', 5, "f-string dans requête SQL"),
            (r'execute\(f\'', 5, "f-string dans requête SQL"),
            (r'execute\(".*%[sd]', 4, "Formatage % dans requête SQL"),
            (r'execute\(.*\.format\(', 4, ".format() dans requête SQL"),
            (r'execute\(".*" \+', 4, "Concaténation + dans requête SQL"),
        ]
        for py_file in ROOT.rglob("*.py"):
            if '.venv' in str(py_file): continue
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern, level, msg in patterns:
                    if re.search(pattern, content):
                        self.add(level, section, msg, str(py_file.relative_to(ROOT)))
            except: pass
        
        # Vérifier que les noms de tables dynamiques ont une whitelist
        for py_file in ROOT.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if re.search(r'execute\(f"[^"]*{', content) or re.search(r"execute\(f'[^']*{", content):
                    self.add(5, section, "Table dynamique sans whitelist", str(py_file.relative_to(ROOT)))
            except: pass
        
        return self
    
    # B. Secrets
    def audit_secrets(self):
        section = "Secrets"
        for py_file in ROOT.rglob("*.py"):
            if '.venv' in str(py_file): continue
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern, level, msg in [
                    (r'password\s*=\s*["\'][^"\'$]{3,}', 4, "Mot de passe en dur"),
                    (r'secret\s*=\s*["\'][^"\'$]{10,}', 4, "Secret en dur"),
                    (r'api_key\s*=\s*["\'][^"\'$]{10,}', 4, "Clé API en dur"),
                    (r'(eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{10,})', 5, "JWT/Token en dur dans le code"),
                ]:
                    matches = re.findall(pattern, content)
                    if matches:
                        self.add(level, section, msg, str(py_file.relative_to(ROOT)), "Déplacer dans config.ini ou variable d'environnement")
            except: pass
        
        # Vérifier SECRET_KEY
        config_file = ROOT / "ArtizBoardCommon" / "config.ini"
        if config_file.exists():
            config = config_file.read_text()
            if "change-me-in-production" in config:
                self.add(5, section, "SECRET_KEY = 'change-me-in-production' (valeur par défaut)", "config.ini", "Générer une clé de 32+ caractères")
            match = re.search(r'jwt_secret_key\s*=\s*(.+)', config)
            if match and len(match.group(1).strip()) < 32:
                self.add(4, section, "SECRET_KEY trop courte (< 32 car.)", "config.ini", "Générer une clé plus longue")
        
        return self
    
    # C. Auth
    def audit_auth(self):
        section = "Authentification"
        auth_file = ROOT / "apps" / "common" / "auth.py"
        if auth_file.exists():
            content = auth_file.read_text()
            if "gensalt()" in content and "rounds" not in content:
                self.add(4, section, "bcrypt.gensalt() sans rounds explicite (défaut=12, OK si >= 12)", "auth.py")
            if "password_hash TEXT" not in (ROOT / "db" / "init_pg_local.sql").read_text():
                self.add(5, section, "password_hash pas présent dans le schéma", "init_pg_local.sql")
            if "ACTIVATION_EXPIRE_MINUTES" in content:
                match = re.search(r'ACTIVATION_EXPIRE_MINUTES\s*=\s*(\d+)', content)
                if match and int(match.group(1)) > 30:
                    self.add(4, section, f"Code activation expire en {match.group(1)} min (> 30 min recommandé)", "auth.py")
        
        return self
    
    # D. Database
    def audit_database(self):
        section = "Base de données"
        init_sql = ROOT / "db" / "init_pg_local.sql"
        if init_sql.exists():
            content = init_sql.read_text()
            if "ON DELETE CASCADE" in content:
                self.add(5, section, "ON DELETE CASCADE détecté", "init_pg_local.sql", "Remplacer par soft delete (deleted_at)")
            if "deleted_at" not in content:
                self.add(5, section, "Pas de colonne deleted_at (soft delete)", "init_pg_local.sql")
            if "version INTEGER DEFAULT 1" not in content:
                self.add(5, section, "Pas de colonne version (optimistic locking)", "init_pg_local.sql")
        
        # PgBouncer
        pgb_file = ROOT / "db" / "pgbouncer.ini"
        if pgb_file.exists():
            content = pgb_file.read_text()
            if "pool_mode = transaction" not in content:
                self.add(4, section, "PgBouncer pas en mode transaction", "pgbouncer.ini")
        
        # Supabase RLS
        sb_sql = ROOT / "db" / "init_supabase.sql"
        if sb_sql.exists():
            content = sb_sql.read_text()
            tables = re.findall(r"CREATE TABLE (\w+)", content)
            rls_tables = re.findall(r"ALTER TABLE (\w+) ENABLE ROW LEVEL SECURITY", content)
            for t in tables:
                if t not in rls_tables and t not in ("schema_version",):
                    self.add(3, section, f"Table {t} sans RLS activé", "init_supabase.sql", "Ajouter ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        
        return self
    
    # E. Input validation
    def audit_inputs(self):
        section = "Validation Entrées"
        for py_file in ROOT.rglob("*.py"):
            if '.venv' in str(py_file): continue
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern, level, msg in [
                    (r'eval\(', 5, "eval() détecté"),
                    (r'exec\(', 5, "exec() détecté"),
                ]:
                    if re.search(pattern, content):
                        self.add(level, section, msg, str(py_file.relative_to(ROOT)))
            except: pass
        
        return self
    
    # F. Dependencies
    def audit_dependencies(self):
        section = "Dépendances"
        try:
            import subprocess
            result = subprocess.run(["pip", "list", "--outdated", "--format=json"], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                import json
                outdated = json.loads(result.stdout)
                for pkg in outdated:
                    self.add(2, section, f"{pkg['name']} {pkg['version']} → {pkg['latest_version']} (mise à jour disponible)")
        except:
            self.pass_(section, "pip list --outdated non disponible")
        
        return self
    
    # G. Frontend
    def audit_frontend(self):
        section = "Frontend/JS"
        for js_file in ROOT.rglob("*.js"):
            if '.venv' in str(js_file) or 'node_modules' in str(js_file): continue
            try:
                content = js_file.read_text(encoding="utf-8")
                for pattern, level, msg in [
                    (r'eval\(', 5, "eval() dans JS"),
                    (r'innerHTML\s*=\s*[^=]', 4, "innerHTML sans échappement"),
                ]:
                    if re.search(pattern, content):
                        self.add(level, section, msg, str(js_file.relative_to(ROOT)))
            except: pass
        
        # Vérifier config.js
        config_js = ROOT / "wp-content" / "themes" / "artizboard" / "assets" / "js" / "config.js"
        if config_js.exists():
            content = config_js.read_text()
            if "service_role" in content.lower() and "SUPABASE" in content:
                self.add(5, section, "service_role key exposée dans config.js (frontend)", "config.js", "Utiliser uniquement la anon_key en frontend")
        
        return self
    
    # H. WordPress
    def audit_wordpress(self):
        section = "WordPress"
        # Vérifier que xmlrpc et REST API ne sont pas exposés dangereusement
        functions = ROOT / "wp-content" / "themes" / "artizboard" / "functions.php"
        if functions.exists():
            content = functions.read_text()
            if "add_action('wp_head'" in content and "wp_generator" not in content:
                self.add(2, section, "Version WordPress exposée dans meta generator", "functions.php", "Ajouter remove_action('wp_head', 'wp_generator')")
        
        return self
    
    def run(self) -> dict:
        self.audit_sql_injection()
        self.audit_secrets()
        self.audit_auth()
        self.audit_database()
        self.audit_inputs()
        self.audit_dependencies()
        self.audit_frontend()
        self.audit_wordpress()
        
        # Trier par niveau décroissant
        self.findings.sort(key=lambda x: -x['level'])
        
        # Générer rapport
        total = len(self.findings)
        critical = sum(1 for f in self.findings if f['level'] == 5)
        high = sum(1 for f in self.findings if f['level'] == 4)
        
        return {
            "total_findings": total,
            "critical": critical,
            "high": high,
            "findings": self.findings,
            "passed": self.passed,
        }
    
    def report(self):
        result = self.run()
        print("\n" + "="*70)
        print("  AUDIT DE SECURITE — ArtizBoard")
        print("="*70)
        print(f"  Vulnérabilités : {result['total_findings']} (🔴{result['critical']} critique, 🟠{result['high']} élevé)")
        print(f"  Contrôles OK : {len(result['passed'])}")
        print("="*70)
        
        if result['findings']:
            level_names = {5: "🔴 CRITIQUE", 4: "🟠 ÉLEVÉ", 3: "🟡 MOYEN", 2: "🔵 FAIBLE", 1: "⚪ INFO"}
            for f in result['findings']:
                print(f"\n  {level_names.get(f['level'], f['level'])} | {f['section']}")
                print(f"  {f['message']}")
                if f['file']: print(f"  Fichier : {f['file']}")
                if f['fix']: print(f"  Correctif : {f['fix']}")
        
        print(f"\n{'='*70}")
        if result['critical'] == 0 and result['high'] == 0:
            print("  [OK] Aucune vulnérabilité critique ou élevée.")
        else:
            print(f"  [ACTION] {result['critical']+result['high']} vulnérabilités à corriger.")
        print("="*70)
        
        return result

if __name__ == "__main__":
    SecurityAudit().report()
```

## 4. Deux exemples

### Exemple 1 — Audit SQL Injection (cas simple)

```bash
$ python audit_securite.py
🔴 CRITIQUE | SQL Injection
f-string dans requête SQL
Fichier : apps/admin/__main__.py
Correctif : Remplacer f"SELECT * FROM {table}" par "SELECT * FROM %s" + paramètres
```

### Exemple 2 — Audit complet (cas complexe)

```bash
$ python audit_securite.py
============================================================
  AUDIT DE SECURITE — ArtizBoard
============================================================
  Vulnérabilités : 12 (🔴2 critique, 🟠4 élevé)
  Contrôles OK : 24
============================================================
🔴 CRITIQUE | Secrets
SECRET_KEY = 'change-me-in-production'
🟠 ÉLEVÉ | Base de données
ON DELETE CASCADE détecté dans init_supabase.sql
...
[ACTION] 6 vulnérabilités à corriger.
```

## 5. Step by Step

| Ordre | Action | Résultat attendu |
|---|---|---|
| 1 | `python audit_securite.py` | Rapport généré |
| 2 | Corriger les 🔴 critiques immédiatement | 0 critique |
| 3 | Corriger les 🟠 élevés | 0 élevé |
| 4 | Re-auditer après corrections | Score amélioré |
| 5 | Ajouter audit au pipeline `livrer.py` | Audit automatique à chaque livraison |

## 6. Checklist

- [ ] Audit SQL injection exécuté
- [ ] Audit secrets exécuté
- [ ] Audit auth exécuté
- [ ] Audit DB exécuté
- [ ] Audit inputs exécuté
- [ ] Audit dépendances exécuté
- [ ] Audit frontend exécuté
- [ ] Audit WordPress exécuté
- [ ] 0 vulnérabilité critique (🔴)
- [ ] 0 vulnérabilité élevée (🟠)

## Emplacement
- Skill : `open-design/skills/securite-audit/SKILL.md`
- Script : `audit_securite.py` (racine)
