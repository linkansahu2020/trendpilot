from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from queue import Queue
from threading import Lock
from uuid import uuid4

# A listener receives this when the job is deleted while it is waiting.
JOB_REMOVED = object()


@dataclass
class Clip:
    index: int
    start: float
    end: float
    hook: str
    title: str
    caption: str
    hashtags: list[str]
    score: int
    path: Path

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class ClipJob:
    id: str
    work_dir: Path
    status: str = "queued"
    progress: float = 0.0
    error: str | None = None
    clips: list[Clip] = field(default_factory=list)


@dataclass
class ClipJobSubscription:
    listener: Queue
    job: ClipJob


class ClipJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, ClipJob] = {}
        self._listeners: dict[str, list[Queue]] = {}
        self._lock = Lock()

    def create(self, work_root: Path) -> ClipJob:
        job_id = uuid4().hex
        work_dir = work_root / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        job = ClipJob(id=job_id, work_dir=work_dir)
        with self._lock:
            self._jobs[job_id] = job
            return replace(job)

    def get(self, job_id: str) -> ClipJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return self._copy(job) if job is not None else None

    def subscribe(self, job_id: str) -> ClipJobSubscription | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            listener: Queue = Queue()
            self._listeners.setdefault(job_id, []).append(listener)
            return ClipJobSubscription(listener=listener, job=self._copy(job))

    def unsubscribe(self, job_id: str, listener: Queue) -> None:
        with self._lock:
            listeners = self._listeners.get(job_id)
            if listeners is None or listener not in listeners:
                return
            listeners.remove(listener)
            if not listeners:
                del self._listeners[job_id]

    def update(self, job_id: str, status: str, progress: float) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = status
                job.progress = progress
                self._publish(job)

    def fail(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = "failed"
                job.error = message
                self._publish(job)

    def add_clip(self, job_id: str, clip: Clip) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.clips.append(clip)
                self._publish(job)

    def remove(self, job_id: str) -> ClipJob | None:
        with self._lock:
            job = self._jobs.pop(job_id, None)
            for listener in self._listeners.pop(job_id, []):
                listener.put(JOB_REMOVED)
            return job

    def _copy(self, job: ClipJob) -> ClipJob:
        return replace(job, clips=list(job.clips))

    def _publish(self, job: ClipJob) -> None:
        snapshot = self._copy(job)
        for listener in self._listeners.get(job.id, []):
            listener.put(snapshot)
