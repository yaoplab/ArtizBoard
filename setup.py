"""ArtizBoard — Database Setup (idempotent)

Creates the PostgreSQL user, database, and runs init_pg_local.sql.
Safe to run multiple times.
    python setup.py
"""

import psycopg2
from pathlib import Path

SUPERUSER = "postgres"
SUPERPASS = "postgres"
HOST = "127.0.0.1"
PORT = 5432

DB_USER = "artizboard"
DB_PASS = "artizboard_pass"
DB_NAME = "artizboard_local"

INIT_SQL = Path(__file__).parent / "db" / "init_pg_local.sql"


def _pg_conn(dbname="postgres"):
    return psycopg2.connect(
        host=HOST, port=PORT, dbname=dbname,
        user=SUPERUSER, password=SUPERPASS,
        client_encoding="UTF8",
    )


def main():
    # ── Create role ──
    conn = _pg_conn()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (DB_USER,))
    if not cur.fetchone():
        cur.execute(f"CREATE ROLE {DB_USER} WITH LOGIN PASSWORD %s", (DB_PASS,))
        print(f"Role '{DB_USER}' cree.")
    else:
        print(f"Role '{DB_USER}' existe deja.")
    cur.close()
    conn.close()

    # ── Create database ──
    conn = _pg_conn()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER}")
        print(f"Base '{DB_NAME}' creee.")
    else:
        print(f"Base '{DB_NAME}' existe deja.")
    cur.close()
    conn.close()

    # ── Run init SQL ──
    if INIT_SQL.exists():
        conn = _pg_conn(DB_NAME)
        conn.autocommit = True
        cur = conn.cursor()
        sql = INIT_SQL.read_text(encoding="utf-8")
        try:
            cur.execute(sql)
            print(f"Schema initialise depuis {INIT_SQL.name}.")
        except (psycopg2.errors.DuplicateTable, psycopg2.errors.DuplicateObject) as e:
            conn.rollback()
            print(f"Schema deja existant ({type(e).__name__}).")
        except Exception as e:
            conn.rollback()
            print(f"Erreur SQL: {e}")
        cur.close()
        conn.close()
    else:
        print(f"ATTENTION: {INIT_SQL} introuvable.")

    # ── Grant permissions ──
    conn = _pg_conn(DB_NAME)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
    cur.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {DB_USER}")
    cur.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {DB_USER}")
    cur.close()
    conn.close()
    print("Permissions accordees.")

    print("\n=== Setup termine. Lancez: python -m admin_app ===")


if __name__ == "__main__":
    main()
