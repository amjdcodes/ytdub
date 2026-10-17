"""قاعدة بيانات السجل (sqlite من المكتبة القياسية).

تحفظ كل رابط مع حالته: pending / success / failed / resumed / retried / skipped
+ عدد المحاولات والمسار النهائي — وتُعرض عبر `ytdub --history`.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from . import config
from .i18n import t

DB_FILENAME = "history.db"

STATUS_PENDING = "pending"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_RESUMED = "resumed"
STATUS_RETRIED = "retried"
STATUS_SKIPPED = "skipped"


def status_label(status: str) -> str:
    """اسم الحالة بلغة الواجهة الحالية."""
    return t(f"status.{status}")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    video_id TEXT DEFAULT '',
    title TEXT DEFAULT '',
    lang TEXT DEFAULT '',
    height INTEGER,
    container TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    filepath TEXT DEFAULT '',
    error TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def db_path() -> str:
    return os.path.join(config.app_dir(), DB_FILENAME)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    os.makedirs(config.app_dir(), exist_ok=True)
    con = sqlite3.connect(db_path())
    con.execute(_SCHEMA)
    con.commit()
    return con


def record_start(url: str, video_id: str = "", title: str = "", lang: str = "", height=None, container: str = "") -> int:
    con = connect()
    try:
        cur = con.execute(
            "INSERT INTO downloads (url, video_id, title, lang, height, container, status, attempts, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)",
            (url, video_id, title, lang, height, container, _now(), _now()),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


def record_attempt(row_id: int, status: str, error: str = "", filepath: str = "") -> None:
    con = connect()
    try:
        con.execute(
            "UPDATE downloads SET status=?, attempts=attempts+1, error=?, "
            "filepath=CASE WHEN ? != '' THEN ? ELSE filepath END, updated_at=? WHERE id=?",
            (status, error, filepath, filepath, _now(), row_id),
        )
        con.commit()
    finally:
        con.close()


def record_skip(url: str, video_id: str = "", title: str = "", lang: str = "", height=None, container: str = "", filepath: str = "") -> int:
    """يسجّل صفًا بحالة skipped (الملف موجود مسبقًا) دون أي محاولة تنزيل."""
    con = connect()
    try:
        cur = con.execute(
            "INSERT INTO downloads (url, video_id, title, lang, height, container, status, attempts, filepath, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)",
            (url, video_id, title, lang, height, container, STATUS_SKIPPED, filepath, _now(), _now()),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


_COLS = "id, url, video_id, title, lang, height, container, status, attempts, filepath, error, updated_at"


def get(row_id: int) -> dict | None:
    """يرجع صفًا واحدًا بمعرّفه، أو None."""
    con = connect()
    try:
        con.row_factory = sqlite3.Row
        row = con.execute(f"SELECT {_COLS} FROM downloads WHERE id=?", (row_id,)).fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def last_failed() -> dict | None:
    """يرجع آخر صف بحالة failed (لـ --retry-last)، أو None."""
    con = connect()
    try:
        con.row_factory = sqlite3.Row
        row = con.execute(
            f"SELECT {_COLS} FROM downloads WHERE status=? ORDER BY id DESC LIMIT 1",
            (STATUS_FAILED,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def recent(limit: int = 20) -> list[dict]:
    con = connect()
    try:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT id, url, title, lang, height, status, attempts, filepath, updated_at"
            " FROM downloads ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()
