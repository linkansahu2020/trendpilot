from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

from app.clipping.gemini import GeminiFailure, encode_proxy
from app.clipping.jobs import Clip, ClipJobStore
from app.clipping.render import render_clip
from app.clipping.select import select_moments
from app.clipping.settings import ClipSettings
from app.clipping.source import check_duration, download
from app.clipping.tools import ClipFailure
from app.clipping.transcribe import transcribe

logger = logging.getLogger(__name__)

# Transcription and rendering saturate the CPU, so jobs run one at a time and wait as "queued".
_run_lock = Lock()


def run_job(store: ClipJobStore, job_id: str, settings: ClipSettings, url: str | None, upload: Path | None) -> None:
    with _run_lock:
        job = store.get(job_id)
        if job is None:
            return
        try:
            failure = _run_steps(store, job_id, job.work_dir, settings, url, upload)
        except Exception:
            logger.exception("Clip job %s crashed", job_id)
            failure = ClipFailure("The clip job failed unexpectedly.")
        if failure is not None:
            store.fail(job_id, failure.message)
        _remove_intermediate_files(job.work_dir)


def _run_steps(
    store: ClipJobStore, job_id: str, folder: Path, settings: ClipSettings, url: str | None, upload: Path | None
) -> ClipFailure | GeminiFailure | None:
    store.update(job_id, "downloading", 0.05)
    source = upload if upload is not None else download(settings, url or "", folder)
    if isinstance(source, ClipFailure):
        return source
    duration = check_duration(settings, source)
    if isinstance(duration, ClipFailure):
        return duration

    store.update(job_id, "transcribing", 0.15)
    segments = transcribe(settings, source, folder)
    if isinstance(segments, ClipFailure):
        return segments

    store.update(job_id, "selecting", 0.4)
    proxy = encode_proxy(settings, source, folder / "proxy.mp4")
    if isinstance(proxy, ClipFailure):
        return proxy
    moments = select_moments(settings, proxy, segments, duration)
    if isinstance(moments, GeminiFailure):
        return moments

    for position, moment in enumerate(moments):
        store.update(job_id, "rendering", 0.6 + 0.4 * position / len(moments))
        index = position + 1
        path = render_clip(settings, source, segments, moment.start, moment.end, index, folder)
        if isinstance(path, ClipFailure):
            return path
        store.add_clip(
            job_id,
            Clip(
                index=index,
                start=moment.start,
                end=moment.end,
                hook=moment.hook,
                title=moment.title,
                caption=moment.caption,
                hashtags=moment.hashtags,
                score=moment.score,
                path=path,
            ),
        )

    store.update(job_id, "done", 1.0)
    return None


def _remove_intermediate_files(folder: Path) -> None:
    if not folder.is_dir():
        return
    for path in folder.iterdir():
        if path.is_file() and not path.name.startswith("clip-"):
            path.unlink(missing_ok=True)
