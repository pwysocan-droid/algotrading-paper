"""Database access and migration runner.

Migrations live in db/migrations/ as paired NNN_name.up.sql / NNN_name.down.sql files.
A schema_migrations table tracks which migrations have been applied; running migrate()
is idempotent.
"""

import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "trader.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "db" / "migrations"

_MIGRATION_FILENAME_RE = re.compile(r"^(\d{3})_([a-z0-9_]+)\.(up|down)\.sql$")


def get_db_path() -> Path:
    override = os.environ.get("TRADER_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_schema_migrations(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )


def _list_migrations(direction: str) -> list[tuple[str, str, Path]]:
    if direction not in ("up", "down"):
        raise ValueError(f"direction must be 'up' or 'down', got {direction!r}")
    found: list[tuple[str, str, Path]] = []
    for path in sorted(MIGRATIONS_DIR.iterdir()):
        m = _MIGRATION_FILENAME_RE.match(path.name)
        if not m:
            continue
        version, name, dir_ = m.groups()
        if dir_ == direction:
            found.append((version, name, path))
    return found


def applied_versions(conn: sqlite3.Connection) -> set[str]:
    _ensure_schema_migrations(conn)
    return {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}


def migrate(db_path: Path | None = None) -> list[str]:
    """Apply all pending up migrations. Returns list of versions applied."""
    applied: list[str] = []
    with connect(db_path) as conn:
        _ensure_schema_migrations(conn)
        already = applied_versions(conn)
        for version, name, path in _list_migrations("up"):
            if version in already:
                continue
            sql = path.read_text()
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (version, name),
            )
            applied.append(version)
    return applied


def rollback(db_path: Path | None = None, steps: int = 1) -> list[str]:
    """Roll back the most recent N up migrations using their .down.sql files.

    Returns list of versions rolled back, in the order rolled back (newest first).
    """
    rolled_back: list[str] = []
    down_by_version: dict[str, Path] = {
        v: p for v, _, p in _list_migrations("down")
    }
    with connect(db_path) as conn:
        _ensure_schema_migrations(conn)
        rows = conn.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version DESC LIMIT ?",
            (steps,),
        ).fetchall()
        for row in rows:
            version = row["version"]
            down_path = down_by_version.get(version)
            if down_path is None:
                raise FileNotFoundError(
                    f"No down migration for version {version} (looked in {MIGRATIONS_DIR})"
                )
            sql = down_path.read_text()
            conn.executescript(sql)
            conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
            rolled_back.append(version)
    return rolled_back


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Trader migration runner")
    parser.add_argument("command", choices=["migrate", "rollback", "status"])
    parser.add_argument("--steps", type=int, default=1, help="rollback step count")
    args = parser.parse_args()

    if args.command == "migrate":
        applied = migrate()
        if applied:
            print(f"Applied {len(applied)} migration(s): {', '.join(applied)}")
        else:
            print("No pending migrations.")
    elif args.command == "rollback":
        rolled = rollback(steps=args.steps)
        if rolled:
            print(f"Rolled back {len(rolled)} migration(s): {', '.join(rolled)}")
        else:
            print("Nothing to roll back.")
    elif args.command == "status":
        with connect() as conn:
            applied = sorted(applied_versions(conn))
            print(f"Applied migrations ({len(applied)}):")
            for v in applied:
                print(f"  {v}")
            print(f"Tables: {', '.join(list_tables(conn))}")
