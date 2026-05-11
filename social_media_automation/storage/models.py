"""SQLite storage layer — schema, migrations, and CRUD helpers."""

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterator, List, Optional


class PostStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(str, Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS posts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    platform      TEXT    NOT NULL,
    content       TEXT    NOT NULL,
    scheduled_at  TEXT    NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'pending',
    published_at  TEXT,
    platform_id   TEXT,       -- ID returned by the platform after publishing
    error_message TEXT,
    retry_count   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS generated_content (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    topic        TEXT NOT NULL,
    platform     TEXT NOT NULL,
    tone         TEXT NOT NULL DEFAULT 'professional',
    content      TEXT NOT NULL,
    used         INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rate_limit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    platform    TEXT NOT NULL,
    endpoint    TEXT NOT NULL,
    request_at  TEXT NOT NULL DEFAULT (datetime('now')),
    reset_at    TEXT
);

CREATE INDEX IF NOT EXISTS idx_posts_status_scheduled
    ON posts (status, scheduled_at);

CREATE INDEX IF NOT EXISTS idx_posts_platform
    ON posts (platform);
"""


@dataclass
class Post:
    id: Optional[int]
    platform: str
    content: str
    scheduled_at: datetime
    status: str = PostStatus.PENDING
    published_at: Optional[datetime] = None
    platform_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class GeneratedContent:
    id: Optional[int]
    topic: str
    platform: str
    tone: str
    content: str
    used: bool = False
    created_at: Optional[datetime] = None


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        with self._lock:
            if self._conn is None:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA foreign_keys=ON")
                self._conn = conn
        return self._conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_schema(self) -> None:
        with self.transaction() as conn:
            conn.executescript(SCHEMA_SQL)

    # ── Post CRUD ──────────────────────────────────────────────────────────

    def create_post(self, post: Post) -> Post:
        sql = """
            INSERT INTO posts (platform, content, scheduled_at, status)
            VALUES (?, ?, ?, ?)
        """
        with self.transaction() as conn:
            cur = conn.execute(
                sql,
                (
                    post.platform,
                    post.content,
                    post.scheduled_at.isoformat(),
                    post.status,
                ),
            )
            post.id = cur.lastrowid
        return post

    def get_post(self, post_id: int) -> Optional[Post]:
        row = self._connect().execute(
            "SELECT * FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        return _row_to_post(row) if row else None

    def list_posts(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Post]:
        conditions, params = [], []
        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params += [limit, offset]
        rows = self._connect().execute(
            f"SELECT * FROM posts {where} ORDER BY scheduled_at ASC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        return [_row_to_post(r) for r in rows]

    def get_due_posts(self, now: datetime) -> List[Post]:
        """Return pending posts whose scheduled_at <= now."""
        rows = self._connect().execute(
            """SELECT * FROM posts
               WHERE status = 'pending' AND scheduled_at <= ?
               ORDER BY scheduled_at ASC""",
            (now.isoformat(),),
        ).fetchall()
        return [_row_to_post(r) for r in rows]

    def update_post_status(
        self,
        post_id: int,
        status: str,
        *,
        platform_id: Optional[str] = None,
        error_message: Optional[str] = None,
        published_at: Optional[datetime] = None,
        retry_count: Optional[int] = None,
    ) -> None:
        fields = ["status = ?", "updated_at = datetime('now')"]
        params: list = [status]

        if platform_id is not None:
            fields.append("platform_id = ?")
            params.append(platform_id)
        if error_message is not None:
            fields.append("error_message = ?")
            params.append(error_message)
        if published_at is not None:
            fields.append("published_at = ?")
            params.append(published_at.isoformat())
        if retry_count is not None:
            fields.append("retry_count = ?")
            params.append(retry_count)

        params.append(post_id)
        with self.transaction() as conn:
            conn.execute(
                f"UPDATE posts SET {', '.join(fields)} WHERE id = ?", params
            )

    def delete_post(self, post_id: int) -> bool:
        with self.transaction() as conn:
            cur = conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        return cur.rowcount > 0

    # ── Generated content ─────────────────────────────────────────────────

    def save_generated_content(self, gc: GeneratedContent) -> GeneratedContent:
        with self.transaction() as conn:
            cur = conn.execute(
                """INSERT INTO generated_content (topic, platform, tone, content)
                   VALUES (?, ?, ?, ?)""",
                (gc.topic, gc.platform, gc.tone, gc.content),
            )
            gc.id = cur.lastrowid
        return gc

    def list_generated_content(
        self, platform: Optional[str] = None, unused_only: bool = False
    ) -> List[GeneratedContent]:
        conditions, params = [], []
        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if unused_only:
            conditions.append("used = 0")
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._connect().execute(
            f"SELECT * FROM generated_content {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [_row_to_generated(r) for r in rows]

    def mark_content_used(self, content_id: int) -> None:
        with self.transaction() as conn:
            conn.execute(
                "UPDATE generated_content SET used = 1 WHERE id = ?", (content_id,)
            )

    # ── Rate-limit logging ────────────────────────────────────────────────

    def log_request(self, platform: str, endpoint: str, reset_at: Optional[str] = None) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO rate_limit_log (platform, endpoint, reset_at) VALUES (?, ?, ?)",
                (platform, endpoint, reset_at),
            )

    def requests_in_window(self, platform: str, endpoint: str, window_seconds: int) -> int:
        """Count requests made to an endpoint within the last window_seconds."""
        row = self._connect().execute(
            """SELECT COUNT(*) as cnt FROM rate_limit_log
               WHERE platform = ? AND endpoint = ?
               AND request_at >= datetime('now', ? || ' seconds')""",
            (platform, endpoint, f"-{window_seconds}"),
        ).fetchone()
        return row["cnt"] if row else 0


# ── Row converters ─────────────────────────────────────────────────────────


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _row_to_post(row: sqlite3.Row) -> Post:
    return Post(
        id=row["id"],
        platform=row["platform"],
        content=row["content"],
        scheduled_at=_parse_dt(row["scheduled_at"]),
        status=row["status"],
        published_at=_parse_dt(row["published_at"]),
        platform_id=row["platform_id"],
        error_message=row["error_message"],
        retry_count=row["retry_count"],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


def _row_to_generated(row: sqlite3.Row) -> GeneratedContent:
    return GeneratedContent(
        id=row["id"],
        topic=row["topic"],
        platform=row["platform"],
        tone=row["tone"],
        content=row["content"],
        used=bool(row["used"]),
        created_at=_parse_dt(row["created_at"]),
    )
