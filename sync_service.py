"""ArtizBoard — Sync Service (Livrable A)

Moteur de synchronisation asynchrone entre PostgreSQL local et Supabase Cloud.

Règles :
- Montée (Local → Cloud) : Unidirectionnelle — toutes les tables sauf commandes.
  commandes est aussi poussée si créée localement (vente sur place).
- Descente (Cloud → Local) : Uniquement les commandes passées via le portail client public.
- Mode 100% intranet : désactivé quand sync_enabled = false dans config.ini.

Usage: python sync_service.py
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection
from supabase import Client, create_client

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ArtizBoardCommon.config_loader import (
    get_db_config,
    get_supabase_config,
    get_sync_config,
)

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [sync] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "sync_service.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("sync_service")


class SyncEngine:
    """Core sync engine — handles the sync logic."""

    def __init__(self):
        db_host, db_port, db_name, db_user, db_pass = get_db_config()
        sb_url, _, sb_service = get_supabase_config()
        cfg = get_sync_config()

        self.enabled = cfg["enabled"]
        self.interval = cfg["interval_seconds"]
        self.tables = cfg["tables"]
        self._stop = False

        # Connect local DB
        self.local: PgConnection = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass,
        )
        self.local.autocommit = False
        logger.info(f"Connected to local DB: {db_host}:{db_port}/{db_name}")

        # Connect Supabase
        self.cloud: Optional[Client] = None
        try:
            self.cloud = create_client(sb_url, sb_service)
            logger.info(f"Connected to Supabase: {sb_url}")
        except Exception as e:
            logger.warning(f"Supabase not reachable: {e}")

        # Sync state file (persists last sync timestamps)
        self.state_file = Path(__file__).parent / ".sync_state.json"
        self.state: dict[str, str] = self._load_state()

    # ── State persistence ──

    def _load_state(self) -> dict[str, str]:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {}

    def _save_state(self):
        self.state_file.write_text(json.dumps(self.state, indent=2))

    # ── Connectivity ──

    async def _is_online(self) -> bool:
        if self.cloud is None:
            return False
        try:
            result = self.cloud.table("schema_version").select("version").limit(1).execute()
            return len(result.data) >= 0  # empty table = ok too
        except Exception as e:
            logger.debug(f"Connectivity check failed: {e}")
            return False

    # ── Helpers ──

    @staticmethod
    def _serialize(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (int, float, str, bool)):
            return value
        if isinstance(value, (dict, list)):
            return value
        return str(value)

    @staticmethod
    def _serialize_row(row: dict) -> dict:
        return {k: SyncEngine._serialize(v) for k, v in row.items()}

    # ── Uplink ──

    async def _push_table(self, table: str) -> int:
        """Push local changes to cloud. Returns number of rows synced."""
        cur = self.local.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        synced = 0
        last_key = f"{table}_last_push"

        try:
            # Find rows to push
            since = self.state.get(last_key, "1970-01-01T00:00:00+00:00")
            cur.execute(
                f"""
                SELECT * FROM "{table}"
                WHERE (sync_status = 'local' OR sync_status = 'pending')
                  AND updated_at > %s
                  AND deleted_at IS NULL
                ORDER BY updated_at ASC
                LIMIT 100
                """,
                (since,),
            )
            rows = cur.fetchall()

            for row in rows:
                record_id: str = str(row["id"])
                row_updated: str = str(row["updated_at"])

                # Mark pending
                cur.execute(
                    f'UPDATE "{table}" SET sync_status = %s WHERE id = %s',
                    ("pending", record_id),
                )
                self.local.commit()

                try:
                    payload = self._serialize_row(dict(row))
                    self.cloud.table(table).upsert(payload).execute()

                    # Mark synced
                    cur.execute(
                        f'UPDATE "{table}" SET sync_status = %s WHERE id = %s',
                        ("synced", record_id),
                    )
                    self.local.commit()
                    synced += 1
                    logger.debug(f"  ↑ {table}/{record_id} → cloud")

                except Exception as e:
                    # Revert to local on failure
                    cur.execute(
                        f'UPDATE "{table}" SET sync_status = %s WHERE id = %s',
                        ("local", record_id),
                    )
                    self.local.commit()
                    logger.error(f"  ✗ {table}/{record_id}: {e}")

            # Update timestamp
            if rows:
                self.state[last_key] = max(r["updated_at"].isoformat() for r in rows)
                self._save_state()

        except Exception as e:
            self.local.rollback()
            logger.error(f"Push {table} error: {e}")
        finally:
            cur.close()

        return synced

    # ── Downlink ──

    async def _pull_commandes(self) -> int:
        """Pull client commandes from cloud into local. Returns count."""
        cur = self.local.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        pulled = 0
        last_key = "commandes_last_pull"

        try:
            since = self.state.get(last_key, "1970-01-01T00:00:00+00:00")

            result = (
                self.cloud.table("commandes")
                .select("*")
                .gt("updated_at", since)
                .is_("deleted_at", "null")
                .order("updated_at", desc=False)
                .limit(50)
                .execute()
            )

            for cmd in result.data:
                cmd_id = cmd["id"]

                cur.execute(
                    "SELECT id, version FROM commandes WHERE id = %s AND deleted_at IS NULL",
                    (cmd_id,),
                )
                local_row = cur.fetchone()

                if local_row is None:
                    # Insert new command from cloud
                    columns = list(cmd.keys())
                    values = list(cmd.values())
                    placeholders = ", ".join(["%s"] * len(columns))
                    cols_str = ", ".join(columns)
                    cur.execute(
                        f"INSERT INTO commandes ({cols_str}) VALUES ({placeholders}) "
                        "ON CONFLICT (id) DO NOTHING",
                        values,
                    )
                    self.local.commit()
                    pulled += 1
                    logger.info(f"  ↓ commande/{cmd_id} → local (new)")

                elif int(local_row["version"]) < int(cmd.get("version", 1)):
                    # Cloud is newer → update local
                    updates = {k: v for k, v in cmd.items() if k not in ("id", "created_by")}
                    set_clause = ", ".join(f"{k} = %s" for k in updates)
                    values = list(updates.values()) + [cmd_id]
                    cur.execute(
                        f"UPDATE commandes SET {set_clause}, updated_at = NOW() "
                        f"WHERE id = %s",
                        values,
                    )
                    self.local.commit()
                    pulled += 1
                    logger.info(f"  ↓ commande/{cmd_id} → local (update, v{cmd.get('version')})")

            # Update timestamp
            if result.data:
                self.state[last_key] = max(
                    r.get("updated_at", "") for r in result.data
                )
                self._save_state()

        except Exception as e:
            self.local.rollback()
            logger.error(f"Pull commandes error: {e}")
        finally:
            cur.close()

        return pulled

    # ── Sync cycle ──

    async def _cycle(self):
        if not self.enabled:
            logger.debug("Sync disabled in config")
            return

        if not await self._is_online():
            logger.debug("Supabase unreachable — skipping cycle")
            return

        total_up = 0
        for table in self.tables:
            n = await self._push_table(table)
            total_up += n

        n = await self._pull_commandes()
        total_down = n

        if total_up or total_down:
            logger.info(f"Cycle: ↑{total_up} ↓{total_down}")

    # ── Public API ──

    async def run(self):
        logger.info(
            f"Sync service started (enabled={self.enabled}, interval={self.interval}s)"
        )
        while not self._stop:
            try:
                await self._cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}", exc_info=True)
            await asyncio.sleep(self.interval)

    def stop(self):
        self._stop = True
        try:
            self.local.close()
        except Exception:
            pass
        logger.info("Sync service stopped")


# ── Entry point ──

async def main():
    engine = SyncEngine()

    # Graceful shutdown on Ctrl+C
    loop = asyncio.get_event_loop()
    for sig in ("SIGINT", "SIGTERM"):
        try:
            loop.add_signal_handler(getattr(__import__("signal"), sig, None) or sig, engine.stop)
        except (ImportError, NotImplementedError):
            pass

    try:
        await engine.run()
    except KeyboardInterrupt:
        engine.stop()


if __name__ == "__main__":
    # Windows compatible
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
