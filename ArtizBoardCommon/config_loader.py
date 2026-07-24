"""Config loader — reads ArtizBoardCommon/config.ini.

Usage:
    from ArtizBoardCommon.config_loader import get_db_config, get_supabase_config
    host, port, name, user, password = get_db_config()
    url, anon_key, service_role_key = get_supabase_config()
"""

import configparser
import os
from pathlib import Path
from typing import Optional


_CONFIG_PATH = Path(__file__).parent / "config.ini"


def _load() -> configparser.ConfigParser:
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {_CONFIG_PATH}")
    cp = configparser.ConfigParser(os.environ)
    cp.read(str(_CONFIG_PATH), encoding="utf-8")
    return cp


def get_db_config() -> tuple[str, int, str, str, str]:
    cp = _load()
    db = cp["database"]
    return (
        db["host"],
        int(db["port"]),
        db["name"],
        db["user"],
        db["password"],
    )


def get_supabase_config() -> tuple[str, str, str]:
    cp = _load()
    sb = cp["supabase"]
    return (
        sb["url"],
        sb["anon_key"],
        sb["service_role_key"],
    )


def get_sync_config() -> dict:
    cp = _load()
    sync = cp["sync"]
    return {
        "enabled": sync.getboolean("enabled", True),
        "interval_seconds": sync.getint("interval_seconds", 10),
        "tables": [t.strip() for t in sync["tables"].split(",")],
    }


def get_auth_config() -> dict:
    cp = _load()
    auth = cp["auth"]
    return {
        "jwt_secret_key": auth["jwt_secret_key"],
        "jwt_algorithm": auth.get("jwt_algorithm", "HS256"),
        "jwt_expiry_minutes": auth.getint("jwt_expiry_minutes", 60),
        "refresh_token_expiry_days": auth.getint("refresh_token_expiry_days", 7),
    }


def get_backup_config() -> dict:
    cp = _load()
    bk = cp["backup"]
    return {
        "directory": Path(bk["directory"]),
        "retention_weekly": bk.getint("retention_weekly", 4),
        "retention_monthly": bk.getint("retention_monthly", 4),
        "retention_yearly": bk.getint("retention_yearly", 1),
        "encryption_passphrase": bk["encryption_passphrase"],
    }


def get_payment_config() -> dict:
    cp = _load()
    pm = cp["payment"]
    return {
        "gateway": pm.get("gateway", "simulated"),
        "tmoney_api_url": pm.get("tmoney_api_url", ""),
        "tmoney_api_key": pm.get("tmoney_api_key", ""),
        "flooz_api_url": pm.get("flooz_api_url", ""),
        "flooz_api_key": pm.get("flooz_api_key", ""),
    }


def get_server_config() -> dict:
    cp = _load()
    sr = cp["server"]
    return {
        "host": sr.get("host", "0.0.0.0"),
        "port": sr.getint("port", 8080),
        "static_dir": Path(sr.get("static_dir", "")),
        "upload_dir": Path(sr.get("upload_dir", "")),
    }
