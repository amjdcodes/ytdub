"""قاعدة بيانات السجل (sqlite من المكتبة القياسية).

تحفظ كل رابط مع حالته: pending / success / failed / resumed / retried
+ عدد المحاولات والمسار النهائي — وتُعرض عبر `ytdub --history`.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from .config import app_dir

DB_FILENAME = "history.db"

STATUS_PENDING = "pending"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_RESUMED = "resumed"
STATUS_RETRIED = "retried"

STATUS_AR = {
    STATUS_PENDING: "قيد الانتظار",
    STATUS_SUCCESS: "نجح ✅",
    STATUS_FAILED: "فشل ❌",
    STATUS_RESUMED: "استُؤنف 🔁",
    STATUS_RETRIED: "أُعيدت محاولته 🔄",
}

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
    return os.path.join(app_dir(), DB_FILENAME)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    os.makedirs(app_dir(), exist_ok=True)
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
