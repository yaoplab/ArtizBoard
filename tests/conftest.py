"""Shared fixtures for ArtizBoard tests."""
import sys, pytest
sys.path.insert(0, r'C:\projet')

import psycopg2, psycopg2.extras
from ArtizBoardCommon.config_loader import get_db_config


@pytest.fixture(scope="session")
def db_conn():
    """PostgreSQL connection (skip if unavailable)."""
    try:
        db = get_db_config()
        conn = psycopg2.connect(host=db[0], port=db[1], dbname=db[2],
                                user=db[3], password=db[4], client_encoding="UTF8")
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")


@pytest.fixture
def cur(db_conn):
    """RealDictCursor for read operations."""
    c = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    yield c
    c.close()


@pytest.fixture
def admin_id(db_conn):
    """Admin user ID from seed data."""
    cur = db_conn.cursor()
    cur.execute("SELECT id FROM utilisateurs WHERE email='admin@larepublique.tg'")
    row = cur.fetchone()
    cur.close()
    return str(row[0]) if row else None


@pytest.fixture
def etab_id(db_conn):
    """Establishment ID from seed data."""
    cur = db_conn.cursor()
    cur.execute("SELECT id FROM etablissements LIMIT 1")
    row = cur.fetchone()
    cur.close()
    return str(row[0]) if row else None


@pytest.fixture
def auth(db_conn):
    """AuthManager instance."""
    from apps.common.auth import AuthManager
    return AuthManager(db_conn)
