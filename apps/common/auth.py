"""ArtizBoard — Authentication Module

Gère l'authentification locale : bcrypt, JWT, activation codes.
Fonctionne en mode 100% intranet (sans Supabase Auth).

Usage:
    from auth import AuthManager
    auth = AuthManager(conn)
    user = auth.login(email, password)         # → jwt_token
    user = auth.activate(code_token, device)    # → jwt_token
    claims = auth.verify_token(jwt_token)       # → dict or None
"""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import bcrypt
import jwt
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection

from ArtizBoardCommon.config_loader import get_auth_config, get_supabase_config

logger = logging.getLogger("auth")

# ── Config ──
_auth_cfg = get_auth_config()
SECRET_KEY = _auth_cfg["jwt_secret_key"]
JWT_ALGORITHM = _auth_cfg["jwt_algorithm"]
JWT_EXPIRY_MINUTES = _auth_cfg["jwt_expiry_minutes"]
REFRESH_EXPIRY_DAYS = _auth_cfg["refresh_token_expiry_days"]

ACTIVATION_EXPIRE_MINUTES = 30
ACTIVATION_MAX_ATTEMPTS = 3


class AuthError(Exception):
    pass


class AuthManager:
    """Local authentication manager."""

    def __init__(self, conn: PgConnection):
        self.conn = conn

    # ── Password hashing ──

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    # ── JWT ──

    @staticmethod
    def create_token(user_id: str, email: str, role: str,
                     etablissement_id: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "etablissement_id": str(etablissement_id),
            "iat": now,
            "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES),
            "jti": secrets.token_hex(8),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # ── Refresh token ──

    def create_refresh_token(self, user_id: str) -> str:
        token = secrets.token_hex(32)
        exp = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRY_DAYS)
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE utilisateurs SET refresh_token = %s, refresh_token_expires_at = %s "
            "WHERE id = %s AND deleted_at IS NULL",
            (token, exp, user_id),
        )
        self.conn.commit()
        cur.close()
        return token

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, email, role_id, etablissement_id FROM utilisateurs "
            "WHERE refresh_token = %s AND refresh_token_expires_at > %s AND deleted_at IS NULL",
            (refresh_token, datetime.now(timezone.utc)),
        )
        user = cur.fetchone()
        cur.close()
        if not user:
            return None

        # Get role name
        cur = self.conn.cursor()
        cur.execute("SELECT nom FROM roles WHERE id = %s", (user["role_id"],))
        role_row = cur.fetchone()
        role = role_row[0] if role_row else "staff"
        cur.close()

        return self.create_token(
            str(user["id"]), user["email"], role, str(user["etablissement_id"])
        )

    def _get_etablissement_nom(self, eid) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT nom FROM etablissements WHERE id = %s", (eid,))
        r = cur.fetchone()
        cur.close()
        return r[0] if r else ""

    # ── Login (email + password) ──

    def login(self, email: str, password: str) -> Tuple[str, str, dict]:
        """Return (access_token, refresh_token, user_info) or raise AuthError."""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT u.id, u.email, u.nom, u.password_hash, u.etablissement_id, "
            "       r.nom AS role "
            "FROM utilisateurs u "
            "JOIN roles r ON u.role_id = r.id "
            "WHERE u.email = %s AND u.deleted_at IS NULL",
            (email,),
        )
        user = cur.fetchone()
        cur.close()

        if not user:
            raise AuthError("Email ou mot de passe incorrect")
        if not user["password_hash"]:
            raise AuthError("Ce compte n'a pas de mot de passe local")

        if not self.verify_password(password, user["password_hash"]):
            raise AuthError("Email ou mot de passe incorrect")

        uid = str(user["id"])
        eid = str(user["etablissement_id"])
        role = user["role"] or "staff"

        access_token = self.create_token(uid, email, role, eid)
        refresh_token = self.create_refresh_token(uid)

        user_info = {
            "id": str(uid), "email": email, "nom": user["nom"],
            "role": role, "etablissement_id": eid,
            "etablissement_nom": self._get_etablissement_nom(eid),
        }
        return access_token, refresh_token, user_info

    # ── Activation code ──

    def generate_activation(self, created_by: str,
                            utilisateur_id: str = None) -> Tuple[str, str]:
        """Generate an activation code. Returns (plain_code, qr_url).

        plain_code: 8-char hex code to display/encode in QR
        qr_url: URL for QR code
        """
        plain = secrets.token_hex(4)  # 8 chars hex
        code_hash = hashlib.sha256(plain.encode()).hexdigest()
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACTIVATION_EXPIRE_MINUTES)

        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO activation_codes (id, code_hash, utilisateur_id, "
            "cree_par, expire_le) VALUES (%s, %s, %s, %s, %s)",
            (str(uuid.uuid4()), code_hash, utilisateur_id, created_by, expire),
        )
        self.conn.commit()
        cur.close()

        # QR URL: get server config
        from ArtizBoardCommon.config_loader import get_server_config
        srv = get_server_config()
        host = srv["host"]
        port = srv["port"]
        qr_url = f"http://{host}:{port}/activate?token={plain}"
        if host == "0.0.0.0":
            qr_url = f"http://192.168.1.1:{port}/activate?token={plain}"

        return plain, qr_url

    def activate_device(self, token: str, device_name: str,
                        device_ip: str) -> Tuple[str, str, dict]:
        """Validate activation code. Return (access_token, refresh_token, user_info).

        Raises AuthError on invalid/expired token.
        """
        code_hash = hashlib.sha256(token.encode()).hexdigest()

        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM activation_codes "
            "WHERE code_hash = %s AND deleted_at IS NULL "
            "AND expire_le > %s AND tentative_count < max_tentatives "
            "AND utilise_le IS NULL",
            (code_hash, datetime.now(timezone.utc)),
        )
        code = cur.fetchone()

        if not code:
            # Increment failed attempts
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE activation_codes SET tentative_count = tentative_count + 1 "
                "WHERE code_hash = %s AND deleted_at IS NULL",
                (code_hash,),
            )
            self.conn.commit()
            cur.close()
            raise AuthError("Code d'activation invalide ou expiré")

        # Mark as used
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE activation_codes SET utilise_le = %s WHERE id = %s",
            (datetime.now(timezone.utc), code["id"]),
        )

        # Register device
        device_id = str(uuid.uuid4())
        uid = code["utilisateur_id"]
        cur.execute(
            "INSERT INTO devices (id, utilisateur_id, device_name, device_ip) "
            "VALUES (%s, %s, %s, %s)",
            (device_id, uid, device_name, device_ip),
        )

        # Update user's device info
        cur.execute(
            "UPDATE utilisateurs SET device_id = %s, device_name = %s, "
            "last_seen_at = %s WHERE id = %s",
            (device_id, device_name, datetime.now(timezone.utc), uid),
        )
        self.conn.commit()
        cur.close()

        # Get user info
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT u.email, u.nom, u.etablissement_id, r.nom AS role "
            "FROM utilisateurs u JOIN roles r ON u.role_id = r.id "
            "WHERE u.id = %s", (uid,),
        )
        user = cur.fetchone()
        cur.close()

        if not user:
            raise AuthError("Utilisateur introuvable")

        access_token = self.create_token(
            str(uid), user["email"], user["role"], str(user["etablissement_id"])
        )
        refresh_token = self.create_refresh_token(str(uid))

        user_info = {
            "id": str(uid), "email": user["email"], "nom": user["nom"],
            "role": user["role"], "etablissement_id": str(user["etablissement_id"]),
            "etablissement_nom": self._get_etablissement_nom(user["etablissement_id"]),
        }
        return access_token, refresh_token, user_info

    def revoke_device(self, device_id: str, revoked_by: str):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE devices SET est_revoque = TRUE, revoque_par = %s, "
            "revoque_le = %s WHERE id = %s",
            (revoked_by, datetime.now(timezone.utc), device_id),
        )
        self.conn.commit()
        cur.close()

    def list_devices(self, etablissement_id: str = None) -> list[dict]:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if etablissement_id:
            cur.execute(
                "SELECT d.*, u.nom AS utilisateur_nom, u.email "
                "FROM devices d JOIN utilisateurs u ON d.utilisateur_id = u.id "
                "WHERE u.etablissement_id = %s AND d.est_revoque = FALSE "
                "ORDER BY d.dernier_acces DESC",
                (etablissement_id,),
            )
        else:
            cur.execute(
                "SELECT d.*, u.nom AS utilisateur_nom, u.email "
                "FROM devices d JOIN utilisateurs u ON d.utilisateur_id = u.id "
                "WHERE d.est_revoque = FALSE ORDER BY d.dernier_acces DESC"
            )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    # ── First boot / Setup ──

    def has_admin(self) -> bool:
        """Check if at least one admin exists."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM utilisateurs u JOIN roles r ON u.role_id = r.id "
            "WHERE r.nom = 'admin' AND u.deleted_at IS NULL LIMIT 1"
        )
        exists = cur.fetchone() is not None
        cur.close()
        return exists

    def create_first_admin(
        self, email: str, password: str, nom: str,
        etablissement_nom: str, etablissement_type: str,
    ) -> Tuple[str, dict]:
        """Create first admin + establishment. Returns (user_id, user_info)."""
        # Create establishment
        eid = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO etablissements (id, nom, type) VALUES (%s, %s, %s)",
            (eid, etablissement_nom, etablissement_type),
        )

        # Get admin role
        cur.execute("SELECT id FROM roles WHERE nom = 'admin'")
        admin_role = cur.fetchone()
        if not admin_role:
            raise AuthError("Rôle 'admin' introuvable — exécutez init_pg_local.sql d'abord")
        role_id = admin_role[0]

        # Create admin user
        uid = str(uuid.uuid4())
        pw_hash = self.hash_password(password)
        cur.execute(
            "INSERT INTO utilisateurs (id, etablissement_id, nom, email, role_id, "
            "password_hash, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (uid, eid, nom, email, role_id, pw_hash, uid),
        )
        self.conn.commit()
        cur.close()

        logger.info(f"First admin created: {email} (etablissement {etablissement_nom})")

        user_info = {
            "id": uid, "email": email, "nom": nom,
            "role": "admin", "etablissement_id": eid,
            "etablissement_nom": etablissement_nom,
        }
        return uid, user_info
