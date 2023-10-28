"""Module for models and database related operations."""
import sqlite3
from contextlib import suppress
from pathlib import Path
from typing import NamedTuple

from pycloudlib.instance import BaseInstance

SCHEMA_VERSION = 1
DB_DIR = Path.home() / ".config" / "jodo"


class InstanceExistsError(Exception):
    """Raised when instance already exists in database."""

    def __init__(self, name: str):
        """Initialize AlreadyExistsError."""
        super().__init__(f"Instance with name '{name}' already exists.")


class InstanceNotFoundError(Exception):
    """Raised when instance cannot be found in database."""

    def __init__(self, name: str):
        """Initialize InstanceNotFoundError."""
        super().__init__(f"Instance '{name}' cannot be found.")


class InstanceInfo(NamedTuple):
    """Instance details."""

    instance_id: str
    name: str
    cloud: str
    ip: str
    port: str
    created: str


def initialize_db(
    db_dir: Path = DB_DIR,
) -> sqlite3.Connection:
    """Initialize database."""
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "jodo.db"

    connection = sqlite3.connect(str(db_path), isolation_level=None)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS instance (
            id TEXT PRIMARY KEY,
            name TEXT,
            cloud TEXT,
            ip TEXT,
            port TEXT,
            created TEXT
        )
    """,
    )
    return connection


connection: sqlite3.Connection = initialize_db()


def ensure_not_exists(name: str) -> None:
    with suppress(InstanceNotFoundError):
        get_info(name)
        raise InstanceExistsError(name)


def create_info(instance: BaseInstance, cloud: str, name: str) -> None:
    """Add newly launched instance to database."""
    ensure_not_exists(name)
    connection.execute(
        "INSERT INTO instance (id, name, cloud, ip, port, created) VALUES "
        "(?, ?, ?, ?, ?, datetime('now')) ",
        (str(instance.id), name, cloud, instance.ip, instance.port),
    )


def list_instances() -> list[InstanceInfo]:
    """List all instances in database."""
    cursor = connection.execute(
        "SELECT id, name, cloud, ip, port, created FROM instance",
    )
    return [InstanceInfo(*i) for i in cursor.fetchall()]


def get_info(name: str) -> InstanceInfo:
    """Get instance from database."""
    result: list[tuple] = connection.execute(
        "SELECT id, name, cloud, ip, port, created FROM instance WHERE name=?",
        (name,),
    ).fetchall()
    rowcount = len(result)
    if rowcount != 1:
        raise InstanceNotFoundError(name)
    return InstanceInfo(*result[0])


def delete_info(name: str) -> None:
    """Delete instance from database."""
    result = connection.execute("DELETE FROM instance WHERE name = ?", (name,))
    if result.rowcount == 0:
        InstanceNotFoundError(name)
    connection.commit()
