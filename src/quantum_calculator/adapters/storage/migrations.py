import sqlite3

_MIGRATIONS: tuple[tuple[str, ...], ...] = (
    (
        """
        CREATE TABLE artifacts (
            sha256 TEXT PRIMARY KEY,
            media_type TEXT NOT NULL,
            size INTEGER NOT NULL
        ) STRICT
        """,
        """
        CREATE TABLE runs (
            identifier TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            origin TEXT NOT NULL,
            parent_identifier TEXT REFERENCES runs (identifier),
            state TEXT NOT NULL,
            card_identifier TEXT NOT NULL,
            card_title TEXT NOT NULL,
            wall_seconds REAL NOT NULL,
            package_version TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            verification_status TEXT,
            failure_category TEXT,
            headline TEXT
        ) STRICT
        """,
        """
        CREATE TABLE run_artifacts (
            run_identifier TEXT NOT NULL REFERENCES runs (identifier),
            role TEXT NOT NULL,
            sha256 TEXT NOT NULL REFERENCES artifacts (sha256),
            PRIMARY KEY (run_identifier, role)
        ) STRICT
        """,
        "CREATE INDEX runs_by_submission ON runs (submitted_at)",
    ),
)

SCHEMA_VERSION = len(_MIGRATIONS)


class NewerHistoryError(Exception):
    def __init__(self, found: int) -> None:
        super().__init__(
            f"the history was written with storage schema {found}, newer than the supported "
            f"schema {SCHEMA_VERSION}"
        )
        self.found = found


def migrate(connection: sqlite3.Connection) -> None:
    (current,) = connection.execute("PRAGMA user_version").fetchone()
    if current > SCHEMA_VERSION:
        raise NewerHistoryError(current)
    for version, statements in enumerate(_MIGRATIONS[current:], start=current + 1):
        for statement in statements:
            connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {version:d}")
