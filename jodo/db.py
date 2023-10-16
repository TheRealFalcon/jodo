"""Module for models and database related operations."""
import sqlite3
from pathlib import Path
from typing import NamedTuple

from pycloudlib.instance import BaseInstance


class InstanceNotFoundError(Exception):
    """Raised when instance cannot be found in database."""

    def __init__(self, name: str):
        """Initialize InstanceNotFoundError."""
        super().__init__(f"Instance {name} cannot be found.")


SCHEMA_VERSION = 1

db_dir = Path.home() / ".config" / "jodo"
db_dir.mkdir(parents=True, exist_ok=True)
db_path = db_dir / "jodo.db"

connection = sqlite3.connect(str(db_path))
cursor = connection.cursor()

cursor.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS instance (
        id TEXT PRIMARY KEY,
        name TEXT,
        cloud TEXT,
        ip TEXT,
        created TEXT
    )
""",
)


class InstanceInfo(NamedTuple):
    """Instance details."""

    instance_id: str
    name: str
    cloud: str
    ip: str
    created: str


def create_instance(instance: BaseInstance, cloud: str, name: str) -> None:
    """Add newly launched instance to database."""
    cursor.execute(
        "INSERT INTO instance (id, name, cloud, ip, created) VALUES "
        "(?, ?, ?, ?, datetime('now')) ",
        (str(instance.id), name, cloud, instance.ip),
    )
    connection.commit()


def list_instances() -> list[InstanceInfo]:
    """List all instances in database."""
    cursor.execute("SELECT id, name, cloud, ip, created FROM instance")
    return [InstanceInfo(*i) for i in cursor.fetchall()]


def get_instance(name: str) -> InstanceInfo:
    """Get instance from database."""
    result: list[tuple] = cursor.execute(
        "SELECT id, name, cloud, ip, created FROM instance WHERE name=?",
        (name,),
    ).fetchall()
    rowcount = len(result)
    if rowcount != 1:
        raise InstanceNotFoundError(name)
    return InstanceInfo(*result[0])


def delete_instance(name: str) -> None:
    """Delete instance from database."""
    result = cursor.execute("Delete from instance")
    connection.commit()
    result = cursor.execute("DELETE FROM instance WHERE name = ?", (name,))
    if result.rowcount == 0:
        InstanceNotFoundError(name)
    connection.commit()
