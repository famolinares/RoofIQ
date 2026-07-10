from dataclasses import dataclass
from pathlib import Path
import sqlite3
from sqlite3 import Connection


@dataclass(frozen=True)
class DatabaseConfig:
    path: Path


def get_connection(config: DatabaseConfig) -> Connection:
    config.path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(config.path)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_database(config: DatabaseConfig) -> None:
    with get_connection(config) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS import_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_filename TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_count INTEGER NOT NULL,
                imported_at TEXT NOT NULL
            );
            """
        )
