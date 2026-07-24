"""Tests for auth module (bcrypt, JWT, QR activation)."""
import sys, pytest, hashlib, re
sys.path.insert(0, r'C:\projet')
from datetime import datetime, timezone


class TestPasswordHashing:
    """bcrypt password hashing."""

    def test_hash_and_verify(self, auth):
        pw = "MonMotDePasse123!"
        hashed = auth.hash_password(pw)
        assert hashed != pw
        assert hashed.startswith("$2b$")
        assert auth.verify_password(pw, hashed) is True
        assert auth.verify_password("wrong", hashed) is False

    def test_hash_is_different_each_time(self, auth):
        h1 = auth.hash_password("test")
        h2 = auth.hash_password("test")
        assert h1 != h2


class TestJWT:
    """JWT token generation and verification."""

    def test_create_token(self, auth):
        token = auth.create_token("user123", "test@test.com", "admin", "etab456")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_verify_valid_token(self, auth):
        token = auth.create_token("user123", "test@test.com", "staff", "etab456")
        claims = auth.verify_token(token)
        assert claims is not None
        assert claims["sub"] == "user123"
        assert claims["email"] == "test@test.com"
        assert claims["role"] == "staff"
        assert claims["etablissement_id"] == "etab456"

    def test_verify_expired_token(self, auth):
        import jwt
        from ArtizBoardCommon.config_loader import get_auth_config
        cfg = get_auth_config()
        from datetime import timedelta
        payload = {"sub": "x", "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
        expired = jwt.encode(payload, cfg["jwt_secret_key"], algorithm=cfg["jwt_algorithm"])
        claims = auth.verify_token(expired)
        assert claims is None

    def test_verify_invalid_token(self, auth):
        claims = auth.verify_token("not.a.token")
        assert claims is None


class TestActivationCode:
    """QR code / activation code flow."""

    def test_generate_and_activate(self, auth, admin_id, db_conn):
        if not admin_id:
            pytest.skip("No admin user found")
        code, url = auth.generate_activation(admin_id, admin_id)
        assert len(code) == 8
        assert re.match(r'^[0-9a-f]{8}$', code)
        assert "http" in url

        access, refresh, info = auth.activate_device(code, "TestPhone", "127.0.0.1")
        assert isinstance(access, str)
        assert isinstance(refresh, str)
        assert info["email"] is not None
        assert info["role"] is not None

    def test_invalid_code_raises_error(self, auth):
        from apps.common.auth import AuthError
        with pytest.raises(AuthError):
            auth.activate_device("badcode1", "Test", "127.0.0.1")

    def test_used_code_cannot_be_reused(self, auth, admin_id):
        if not admin_id:
            pytest.skip("No admin")
        code, _ = auth.generate_activation(admin_id, admin_id)
        auth.activate_device(code, "Phone1", "127.0.0.1")
        from apps.common.auth import AuthError
        with pytest.raises(AuthError):
            auth.activate_device(code, "Phone2", "127.0.0.1")


class TestLogin:
    """Email/password login flow."""

    def test_login_valid(self, auth):
        user = auth.login("admin@larepublique.tg", "admin123")
        assert len(user) == 3
        access, refresh, info = user
        assert isinstance(access, str)
        assert info["email"] == "admin@larepublique.tg"

    def test_login_bad_password(self, auth):
        from apps.common.auth import AuthError
        with pytest.raises(AuthError):
            auth.login("admin@larepublique.tg", "wrongpass")

    def test_login_bad_email(self, auth):
        from apps.common.auth import AuthError
        with pytest.raises(AuthError):
            auth.login("nonexistent@test.com", "anypass")


class TestRefreshToken:
    """Refresh token rotation."""

    def test_create_and_use(self, auth, admin_id):
        if not admin_id:
            pytest.skip("No admin")
        refresh = auth.create_refresh_token(admin_id)
        assert isinstance(refresh, str)
        assert len(refresh) == 64

        new_access = auth.refresh_access_token(refresh)
        assert isinstance(new_access, str)

    def test_invalid_refresh_returns_none(self, auth):
        result = auth.refresh_access_token("invalid_refresh_token")
        assert result is None


class TestDeviceManagement:
    """Device listing and revocation."""

    def test_list_devices(self, auth, etab_id):
        devices = auth.list_devices(etab_id)
        assert isinstance(devices, list)

    def test_revoke_device(self, auth, admin_id, db_conn):
        if not admin_id:
            pytest.skip("No admin")
        cur = db_conn.cursor()
        cur.execute("SELECT id FROM devices LIMIT 1")
        dev = cur.fetchone()
        cur.close()
        if dev:
            auth.revoke_device(str(dev[0]), admin_id)
