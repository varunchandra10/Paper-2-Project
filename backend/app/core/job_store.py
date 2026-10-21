"""Persistent Job Store backed by SQLite with WAL mode.
Provides persistent job tracking, truthful lifecycle status, zombie recovery,
and cancellation semantics.
"""

import os
import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from collections.abc import MutableMapping

from app.core.config import settings


class JobStatus:
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    ACTIVE_STATUSES = {PENDING, QUEUED, PROCESSING, RUNNING}
    TERMINAL_STATUSES = {COMPLETED, FAILED, CANCELLED}


@dataclass
class JobRecord:
    job_id: str
    paper_id: str
    status: str = JobStatus.QUEUED
    progress: float = 0.0
    current_stage: str = "initialized"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cancellation_requested: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["cancellation_requested"] = bool(self.cancellation_requested)
        return d

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "JobRecord":
        result_val = None
        if row["result"]:
            try:
                result_val = json.loads(row["result"])
            except Exception:
                result_val = {"raw": row["result"]}

        return cls(
            job_id=row["job_id"],
            paper_id=row["paper_id"],
            status=row["status"],
            progress=float(row["progress"]),
            current_stage=row["current_stage"],
            result=result_val,
            error=row["error"],
            retry_count=int(row["retry_count"]),
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            updated_at=row["updated_at"],
            cancellation_requested=bool(row["cancellation_requested"]),
        )


class JobStore:
    """Thread-safe, SQLite-backed job persistence store."""

    _instance_lock = threading.Lock()

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(settings.STORAGE_DIR, "jobs.db")

        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Yields an SQLite connection configured with WAL mode and row factory."""
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0.0,
                    current_stage TEXT NOT NULL DEFAULT 'initialized',
                    result TEXT,
                    error TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    updated_at TEXT NOT NULL,
                    cancellation_requested INTEGER NOT NULL DEFAULT 0
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_paper_id ON jobs(paper_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at);")

            # Phase 9: Event-Driven Observability persistent event log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    paper_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    node_name TEXT,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0.0,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_job_events_job_id_id ON job_events(job_id, id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_job_events_timestamp ON job_events(timestamp);")
            conn.commit()

    def create_job(
        self,
        paper_id: str,
        job_id: Optional[str] = None,
        initial_stage: str = "initialized",
        progress: float = 0.0,
        status: str = JobStatus.QUEUED
    ) -> JobRecord:
        if not job_id:
            import uuid
            job_id = f"job_{uuid.uuid4().hex[:8]}"

        now = datetime.now(timezone.utc).isoformat()
        record = JobRecord(
            job_id=job_id,
            paper_id=paper_id,
            status=status,
            progress=progress,
            current_stage=initial_stage,
            created_at=now,
            updated_at=now,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs (
                    job_id, paper_id, status, progress, current_stage,
                    result, error, retry_count, created_at, started_at,
                    completed_at, updated_at, cancellation_requested
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.job_id,
                    record.paper_id,
                    record.status,
                    record.progress,
                    record.current_stage,
                    json.dumps(record.result) if record.result is not None else None,
                    record.error,
                    record.retry_count,
                    record.created_at,
                    record.started_at,
                    record.completed_at,
                    record.updated_at,
                    1 if record.cancellation_requested else 0,
                ),
            )
            conn.commit()

        return record

    def get_job(self, job_or_paper_id: str) -> Optional[JobRecord]:
        """Looks up job by canonical job_id first; falls back to most recent job for paper_id."""
        with self._get_connection() as conn:
            # 1. Look up by job_id
            cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ? LIMIT 1", (job_or_paper_id,))
            row = cursor.fetchone()
            if row:
                return JobRecord.from_row(row)

            # 2. Look up by paper_id (order by created_at/rowid DESC to get most recent)
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE paper_id = ? ORDER BY rowid DESC LIMIT 1",
                (job_or_paper_id,),
            )
            row = cursor.fetchone()
            if row:
                return JobRecord.from_row(row)

        return None

    def get_active_job_for_paper(self, paper_id: str) -> Optional[JobRecord]:
        """Returns any active (queued, pending, processing, running) job for the given paper."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM jobs
                WHERE paper_id = ?
                  AND status IN ('queued', 'pending', 'processing', 'running')
                  AND cancellation_requested = 0
                ORDER BY rowid DESC LIMIT 1
                """,
                (paper_id,),
            )
            row = cursor.fetchone()
            if row:
                return JobRecord.from_row(row)
        return None

    def update_stage(
        self,
        job_id: str,
        stage: str,
        progress: float,
        status: Optional[str] = None
    ) -> Optional[JobRecord]:
        """Updates progress, current stage, and optionally changes status."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            if status:
                started_sql = ", started_at = COALESCE(started_at, ?)" if status in (JobStatus.PROCESSING, JobStatus.RUNNING) else ""
                params = [stage, progress, status, now]
                if started_sql:
                    params.append(now)
                params.append(job_id)

                conn.execute(
                    f"""
                    UPDATE jobs
                    SET current_stage = ?,
                        progress = ?,
                        status = ?,
                        updated_at = ?
                        {started_sql}
                    WHERE job_id = ?
                    """,
                    params,
                )
            else:
                conn.execute(
                    """
                    UPDATE jobs
                    SET current_stage = ?,
                        progress = ?,
                        updated_at = ?
                    WHERE job_id = ?
                    """,
                    (stage, progress, now, job_id),
                )
            conn.commit()

        return self.get_job(job_id)

    def complete_job(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> Optional[JobRecord]:
        now = datetime.now(timezone.utc).isoformat()
        res_str = json.dumps(result) if result is not None else None
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?,
                    progress = 100.0,
                    current_stage = 'completed',
                    result = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (JobStatus.COMPLETED, res_str, now, now, job_id),
            )
            conn.commit()
        return self.get_job(job_id)

    def fail_job(self, job_id: str, error: str) -> Optional[JobRecord]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?,
                    current_stage = 'failed',
                    error = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (JobStatus.FAILED, error, now, now, job_id),
            )
            conn.commit()
        return self.get_job(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Flags job as cancellation requested and marks status as cancelled if not already terminal."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT status FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return False

            current_status = row["status"]
            if current_status in JobStatus.TERMINAL_STATUSES:
                # Already terminal, cannot cancel
                return False

            conn.execute(
                """
                UPDATE jobs
                SET cancellation_requested = 1,
                    status = ?,
                    current_stage = 'cancelled',
                    completed_at = ?,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (JobStatus.CANCELLED, now, now, job_id),
            )
            conn.commit()
        return True

    def is_cancellation_requested(self, job_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT cancellation_requested, status FROM jobs WHERE job_id = ?",
                (job_id,),
            )
            row = cursor.fetchone()
            if row:
                return bool(row["cancellation_requested"]) or row["status"] == JobStatus.CANCELLED
        return False

    def recover_stale_jobs(self, error_msg: str = "Server restarted during execution") -> int:
        """Recovers zombie jobs left in active status (queued/processing/running) after server restart."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE jobs
                SET status = ?,
                    current_stage = 'server_restart_recovered',
                    error = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE status IN ('queued', 'pending', 'processing', 'running')
                """,
                (JobStatus.FAILED, error_msg, now, now),
            )
            recovered_count = cursor.rowcount
            conn.commit()
        return recovered_count

    def list_jobs(self, paper_id: Optional[str] = None, limit: int = 50) -> List[JobRecord]:
        with self._get_connection() as conn:
            if paper_id:
                cursor = conn.execute(
                    "SELECT * FROM jobs WHERE paper_id = ? ORDER BY rowid DESC LIMIT ?",
                    (paper_id, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM jobs ORDER BY rowid DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            return [JobRecord.from_row(r) for r in rows]

    def record_event(
        self,
        job_id: str,
        paper_id: str,
        event_type: str,
        node_name: Optional[str] = None,
        status: str = "success",
        progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> int:
        """
        Appends an immutable, ordered event to the job_events table.
        Updates job's current progress and stage in jobs table if progress/stage provided.
        Returns the monotonic integer event_id.
        """
        now = timestamp or datetime.now(timezone.utc).isoformat()
        meta_str = json.dumps(metadata) if metadata is not None else None

        with self._get_connection() as conn:
            # Determine progress if not supplied
            cur_prog = progress
            if cur_prog is None:
                cursor = conn.execute("SELECT progress FROM jobs WHERE job_id = ? LIMIT 1", (job_id,))
                row = cursor.fetchone()
                cur_prog = float(row["progress"]) if row else 0.0

            cursor = conn.execute(
                """
                INSERT INTO job_events (
                    job_id, paper_id, event_type, node_name, status,
                    progress, timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (job_id, paper_id, event_type, node_name, status, cur_prog, now, meta_str)
            )
            event_id = cursor.lastrowid

            # Keep jobs table synchronized with truthful state
            stage_update = node_name or event_type
            conn.execute(
                """
                UPDATE jobs
                SET current_stage = ?,
                    progress = MAX(progress, ?),
                    updated_at = ?
                WHERE job_id = ?
                """,
                (stage_update, cur_prog, now, job_id)
            )
            conn.commit()

        return event_id

    def get_events(self, job_id: str, since_id: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieves all ordered events for a job strictly with id > since_id.
        Guarantees ordering and enables idempotent SSE client catch-up without duplicates.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, job_id, paper_id, event_type, node_name, status,
                       progress, timestamp, metadata
                FROM job_events
                WHERE job_id = ? AND id > ?
                ORDER BY id ASC
                """,
                (job_id, since_id)
            )
            events = []
            for row in cursor.fetchall():
                meta = None
                if row["metadata"]:
                    try:
                        meta = json.loads(row["metadata"])
                    except Exception:
                        meta = {"raw": row["metadata"]}
                events.append({
                    "event_id": row["id"],
                    "job_id": row["job_id"],
                    "paper_id": row["paper_id"],
                    "event": row["event_type"],
                    "event_type": row["event_type"],
                    "node": row["node_name"],
                    "status": row["status"],
                    "progress": float(row["progress"]),
                    "timestamp": row["timestamp"],
                    "metadata": meta or {}
                })
            return events

    def delete_job(self, job_id: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM job_events WHERE job_id = ?", (job_id,))
            cursor = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            conn.commit()
            return cursor.rowcount > 0


class JobStoreDictWrapper(MutableMapping):
    """Dictionary-compatible wrapper over JobStore for backwards-compatibility with legacy code."""

    def __init__(self, store: JobStore):
        self._store = store

    def __getitem__(self, key: str) -> dict:
        job = self._store.get_job(key)
        if job is None:
            raise KeyError(key)
        return job.to_dict()

    def __setitem__(self, key: str, value: dict):
        # Update or create job record
        existing = self._store.get_job(key)
        paper_id = value.get("paper_id", key)
        status = value.get("status", JobStatus.QUEUED)
        progress = float(value.get("progress", 0.0))
        stage = value.get("current_stage", "updated")
        error = value.get("error")

        if existing and existing.job_id == key:
            if status == JobStatus.COMPLETED:
                self._store.complete_job(key, result=value.get("result"))
            elif status == JobStatus.FAILED:
                self._store.fail_job(key, error=error or "Failed")
            elif status == JobStatus.CANCELLED:
                self._store.cancel_job(key)
            else:
                self._store.update_stage(key, stage=stage, progress=progress, status=status)
        else:
            self._store.create_job(
                paper_id=paper_id,
                job_id=key,
                initial_stage=stage,
                progress=progress,
                status=status
            )
            if error:
                self._store.fail_job(key, error=error)
            elif status == JobStatus.COMPLETED:
                self._store.complete_job(key, result=value.get("result"))

    def __delitem__(self, key: str):
        if not self._store.delete_job(key):
            raise KeyError(key)

    def __iter__(self):
        jobs = self._store.list_jobs(limit=100)
        return iter(j.job_id for j in jobs)

    def __len__(self) -> int:
        jobs = self._store.list_jobs(limit=1000)
        return len(jobs)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return self._store.get_job(key) is not None

    def get(self, key: str, default: Any = None) -> Any:
        job = self._store.get_job(key)
        if job is None:
            return default
        return job.to_dict()

    def record_event(self, *args, **kwargs):
        return self._store.record_event(*args, **kwargs)

    def get_events(self, *args, **kwargs):
        return self._store.get_events(*args, **kwargs)


_global_job_store: Optional[JobStore] = None


def get_job_store(db_path: Optional[str] = None) -> JobStore:
    global _global_job_store
    if _global_job_store is None:
        with JobStore._instance_lock:
            if _global_job_store is None:
                _global_job_store = JobStore(db_path)
    return _global_job_store
