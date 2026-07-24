# Skill: Auth Locale

## 0. Contexte

**Projet** : ArtizBoard
**Module** : `apps/common/auth.py` — authentification locale
**Utilisateurs** : Admin (gère), Staff (s'authentifie)
**Dépendances** : [[crud-m3]] (pour la DB), `config.ini` (SECRET_KEY)
**Prérequis** : PostgreSQL local + table `utilisateurs` créée


## 1. Fonction Principale

### Type : Système Fermé

```
ENTRÉE                              →  TRAITEMENT                        →  SORTIE
email/mot de passe (login)             bcrypt verify + JWT sign          ├─ access_token (JWT)
activation token hex (QR)              SHA-256 match + device register   ├─ refresh_token
user_id + role + etablissement_id      create_token()                    └─ user_info dict
```

## 2. Contraintes Fonctionnelles

### Tableau global

| # | Contrainte |
|---|---|
| C1 | Les mots de passe sont hashés avec **bcrypt** (jamais en clair, jamais SHA/MD5) |
| C2 | Les JWT sont signés avec `SECRET_KEY` lue dans `config.ini`, algorithme HS256 |
| C3 | Le JWT expire après `JWT_EXPIRY_MINUTES` (défaut 60 min), contenu : sub, email, role, etablissement_id |
| C4 | Le refresh token est une chaîne hex 32 octets stockée en base avec date d'expiration |
| C5 | En cas d'échec de connexion (3 tentatives), un délai progressif est appliqué (5s, 15s, 60s) |
| C6 | La vérification de token retourne `None` pour token expiré ou invalide (pas d'exception) |
| C7 | Le mode offline fonctionne sans Supabase : l'auth locale est la seule autorité |

### Sous-système A — Login email/mot de passe

| # | Contrainte |
|---|---|
| A1 | `login(email, password)` retourne `(access_token, refresh_token, user_info)` |
| A2 | En cas d'échec, lève `AuthError` avec message en français |
| A3 | Le mot de passe est vérifié via `bcrypt.checkpw()` |
| A4 | La requête SQL joint `roles` pour obtenir le nom du rôle |

### Sous-système B — Activation QR code

| # | Contrainte |
|---|---|
| B1 | `generate_activation(created_by, user_id)` retourne `(plain_code, qr_url)` |
| B2 | Le code est `secrets.token_hex(4)` = 8 caractères hex = 64 bits d'entropie |
| B3 | Le code est hashé SHA-256 avant stockage (irréversible) |
| B4 | Durée de validité : `ACTIVATION_EXPIRE_MINUTES` (défaut 30 min) |
| B5 | Maximum 3 tentatives (`max_tentatives`), compte incrémenté à chaque échec |
| B6 | L'URL du QR utilise `get_server_config()` pour construire `http://{host}:{port}/activate?token={code}` |

### Sous-système C — Gestion des devices

| # | Contrainte |
|---|---|
| C1 | `activate_device(token, device_name, device_ip)` → crée l'entrée dans `devices` |
| C2 | `revoke_device(device_id, revoked_by)` → flag `est_revoque = TRUE` |
| C3 | `list_devices(etablissement_id)` → retourne les devices non révoqués |

## 3. Code complet

### Imports et config

```python
import hashlib, logging, secrets, uuid
from datetime import datetime, timedelta, timezone
import bcrypt, jwt, psycopg2, psycopg2.extras
from ArtizBoardCommon.config_loader import get_auth_config

_auth = get_auth_config()
SECRET_KEY = _auth["jwt_secret_key"]
JWT_ALGORITHM = _auth["jwt_algorithm"]
JWT_EXPIRY_MINUTES = _auth["jwt_expiry_minutes"]
ACTIVATION_EXPIRE_MINUTES = 30
ACTIVATION_MAX_ATTEMPTS = 3

class AuthError(Exception): pass
```

### AuthManager

```python
class AuthManager:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def create_token(user_id, email, role, etablissement_id) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id), "email": email, "role": role,
            "etablissement_id": str(etablissement_id),
            "iat": now, "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES),
            "jti": secrets.token_hex(8),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict | None:
        try: return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError): return None

    # ── Login ──
    def login(self, email, password) -> tuple[str, str, dict]:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT u.id, u.email, u.nom, u.password_hash, u.etablissement_id, r.nom AS role
            FROM utilisateurs u JOIN roles r ON u.role_id = r.id
            WHERE u.email = %s AND u.deleted_at IS NULL
        """, (email,))
        user = cur.fetchone(); cur.close()
        if not user or not self.verify_password(password, user["password_hash"]):
            raise AuthError("Email ou mot de passe incorrect")
        access = self.create_token(user["id"], email, user["role"], user["etablissement_id"])
        refresh = self.create_refresh_token(user["id"])
        return access, refresh, {"id": str(user["id"]), "email": email, "nom": user["nom"],
                                  "role": user["role"], "etablissement_id": str(user["etablissement_id"])}

    # ── Activation ──
    def generate_activation(self, created_by, utilisateur_id=None) -> tuple[str, str]:
        plain = secrets.token_hex(4)
        code_hash = hashlib.sha256(plain.encode()).hexdigest()
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACTIVATION_EXPIRE_MINUTES)
        cur = self.conn.cursor()
        cur.execute("""INSERT INTO activation_codes (id, code_hash, utilisateur_id, cree_par, expire_le)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (str(uuid.uuid4()), code_hash, utilisateur_id, created_by, expire))
        self.conn.commit(); cur.close()
        from ArtizBoardCommon.config_loader import get_server_config
        s = get_server_config()
        return plain, f"http://{s['host']}:{s['port']}/activate?token={plain}"

    def activate_device(self, token, device_name, device_ip) -> tuple[str, str, dict]:
        code_hash = hashlib.sha256(token.encode()).hexdigest()
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT * FROM activation_codes WHERE code_hash=%s AND deleted_at IS NULL
                       AND expire_le > %s AND tentative_count < max_tentatives AND utilise_le IS NULL""",
                    (code_hash, datetime.now(timezone.utc)))
        code = cur.fetchone()
        if not code: raise AuthError("Code d'activation invalide ou expire")
        cur = self.conn.cursor()
        cur.execute("UPDATE activation_codes SET utilise_le=%s WHERE id=%s",
                    (datetime.now(timezone.utc), code["id"]))
        device_id = str(uuid.uuid4())
        cur.execute("INSERT INTO devices (id, utilisateur_id, device_name, device_ip) VALUES (%s,%s,%s,%s)",
                    (device_id, code["utilisateur_id"], device_name, device_ip))
        self.conn.commit(); cur.close()
        # Get user info and create tokens
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT u.email, u.etablissement_id, r.nom AS role
                       FROM utilisateurs u JOIN roles r ON u.role_id = r.id WHERE u.id=%s""",
                    (code["utilisateur_id"],))
        u = cur.fetchone(); cur.close()
        access = self.create_token(code["utilisateur_id"], u["email"], u["role"], str(u["etablissement_id"]))
        refresh = self.create_refresh_token(code["utilisateur_id"])
        return access, refresh, {"id": str(code["utilisateur_id"]), "email": u["email"],
                                  "role": u["role"], "etablissement_id": str(u["etablissement_id"])}

    # ── Refresh ──
    def create_refresh_token(self, user_id) -> str:
        token = secrets.token_hex(32)
        cur = self.conn.cursor()
        cur.execute("UPDATE utilisateurs SET refresh_token=%s, refresh_token_expires_at=%s WHERE id=%s",
                    (token, datetime.now(timezone.utc) + timedelta(days=7), user_id))
        self.conn.commit(); cur.close()
        return token

    def refresh_access_token(self, refresh_token) -> str | None:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT id, email, role_id, etablissement_id FROM utilisateurs
                       WHERE refresh_token=%s AND refresh_token_expires_at > %s""",
                    (refresh_token, datetime.now(timezone.utc)))
        user = cur.fetchone(); cur.close()
        if not user: return None
        cur = self.conn.cursor(); cur.execute("SELECT nom FROM roles WHERE id=%s", (user["role_id"],))
        role = cur.fetchone()[0]; cur.close()
        return self.create_token(user["id"], user["email"], role, str(user["etablissement_id"]))

    # ── Devices ──
    def revoke_device(self, device_id, revoked_by):
        cur = self.conn.cursor()
        cur.execute("UPDATE devices SET est_revoque=TRUE, revoque_par=%s, revoque_le=%s WHERE id=%s",
                    (revoked_by, datetime.now(timezone.utc), device_id))
        self.conn.commit(); cur.close()

    def list_devices(self, etablissement_id) -> list[dict]:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT d.*, u.nom AS utilisateur_nom FROM devices d
                       JOIN utilisateurs u ON d.utilisateur_id = u.id
                       WHERE u.etablissement_id=%s AND d.est_revoque=FALSE""", (etablissement_id,))
        rows = [dict(r) for r in cur.fetchall()]; cur.close()
        return rows

    # ── First admin ──
    def has_admin(self) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM utilisateurs u JOIN roles r ON u.role_id=r.id WHERE r.nom='admin' LIMIT 1")
        r = cur.fetchone() is not None; cur.close()
        return r

    def create_first_admin(self, email, password, nom, etablissement_nom, etablissement_type):
        eid = str(uuid.uuid4()); cur = self.conn.cursor()
        cur.execute("INSERT INTO etablissements (id, nom, type) VALUES (%s,%s,%s)",
                    (eid, etablissement_nom, etablissement_type))
        cur.execute("SELECT id FROM roles WHERE nom='admin'")
        role = cur.fetchone()
        if not role: raise AuthError("Role admin introuvable")
        uid = str(uuid.uuid4())
        cur.execute("""INSERT INTO utilisateurs (id, etablissement_id, nom, email, role_id, password_hash, created_by)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (uid, eid, nom, email, role[0], self.hash_password(password), uid))
        self.conn.commit(); cur.close()
        return uid, {"id": uid, "email": email, "nom": nom, "role": "admin", "etablissement_id": eid}
```

## 4. Deux exemples

### Exemple 1 — Login simple (cas nominal)

```python
auth = AuthManager(conn)
try:
    access, refresh, user = auth.login("admin@restaurant.tg", "admin123")
    print(f"Connecte: {user['nom']} ({user['role']})")
    claims = AuthManager.verify_token(access)
    print(f"Token valide, expire a: {claims['exp']}")
except AuthError as e:
    print(f"Echec: {e}")
```

### Exemple 2 — Activation QR code (cas complexe)

```python
# Admin genere le code
code, url = auth.generate_activation(admin_id, staff_id)
print(f"Code: {code}")  # "a1b2c3d4"
print(f"QR URL: {url}")  # http://192.168.1.1:8080/activate?token=a1b2c3d4

# Staff active avec le token (scan QR ou saisie manuelle)
try:
    access, refresh, info = auth.activate_device(code, "Tablette Cuisine", "192.168.1.50")
    print(f"Device active pour: {info['nom']}")
except AuthError as e:
    print(f"Code invalide: {e}")
```

## 5. Step by Step — Implementation

| Ordre | Action | Fichier | Resultat |
|---|---|---|---|
| 1 | Configurer SECRET_KEY dans config.ini | `config.ini` | Clé de 32+ caractères |
| 2 | Implémenter hash_password + create_token | `auth.py` | bcrypt + JWT fonctionnels |
| 3 | Implémenter login(email, password) | `auth.py` | Retourne access_token |
| 4 | Implémenter generate_activation | `auth.py` | Code hex + QR URL générés |
| 5 | Implémenter activate_device | `auth.py` | Device enregistré en DB |
| 6 | Implémenter create_first_admin | `auth.py` | Établissement + admin créés |
| 7 | Tester : login valide, mdp erroné, code expiré | `pytest tests/test_auth.py` | 16 tests verts |

## Checklist

- [ ] bcrypt, pas de stockage en clair
- [ ] JWT signé avec SECRET_KEY de config.ini
- [ ] Activation code : 8 hex, SHA-256, 30 min, 3 tentatives
- [ ] Device registration : nom, IP, est_revoque
- [ ] Refresh token : 32 octets hex, expiration 7 jours
- [ ] First admin : crée établissement + admin + rôle
- [ ] Mode offline : fonctionne sans Supabase

## Emplacement
- `apps/common/auth.py` — importable par Admin, Staff
