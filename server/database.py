"""
SQLite message persistence.

Stores all messages in a single continuous stream (no sessions).
Uses aiosqlite for async access.

Usage:
    from server.database import init_db, close_db, append_message, get_recent_messages

    await init_db()                          # call at startup
    await append_message("user", "hello")    # store a message
    msgs = await get_recent_messages(50)     # last 50 messages as (role, content)
    await close_db()                         # call at shutdown
"""

import aiosqlite

from server.config import PROJECT_ROOT, get_config

_db: aiosqlite.Connection | None = None

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db() -> None:
    """Create data directory and messages table. Call once at startup."""
    global _db
    config = get_config()
    data_dir = PROJECT_ROOT / config.server.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "ace.db"
    _db = await aiosqlite.connect(str(db_path))
    await _db.execute(_CREATE_TABLE)
    await _db.commit()


async def close_db() -> None:
    """Close the database connection. Call once at shutdown."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


async def append_message(role: str, content: str) -> None:
    """Insert a message into the continuous stream."""
    assert _db is not None, "Database not initialized — call init_db() first"
    await _db.execute(
        "INSERT INTO messages (role, content) VALUES (?, ?)",
        (role, content),
    )
    await _db.commit()


async def get_recent_messages(limit: int) -> list[tuple[str, str]]:
    """Return the last `limit` messages ordered oldest-first.

    Returns:
        List of (role, content) tuples.
    """
    assert _db is not None, "Database not initialized — call init_db() first"
    cursor = await _db.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = await cursor.fetchall()
    return list(reversed(rows))
