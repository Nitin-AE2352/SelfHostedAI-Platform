
import sqlite3
from pathlib import Path

from app.core.config import settings
from app.core.security import hash_password, verify_password


def _database_file() -> Path:
    path = Path(settings.database_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(
        str(_database_file()),
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    return connection


def initialize_auth_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_user_by_username(username: str) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, username, password_hash, role, created_at
            FROM users
            WHERE username = ?
            """,
            (username.strip(),),
        ).fetchone()

    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, username, role, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    return dict(row) if row else None


def register_user(username: str, password: str) -> dict:
    username = username.strip()

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, 'user')
            """,
            (username, hash_password(password)),
        )
        user_id = cursor.lastrowid

    user = get_user_by_id(int(user_id))
    if user is None:
        raise RuntimeError("Registered user could not be retrieved.")

    return user


def authenticate_user(username: str, password: str) -> dict | None:
    user = get_user_by_username(username)

    if user is None:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"],
    }


initialize_auth_database()
