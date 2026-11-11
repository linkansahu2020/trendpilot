from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from starlette.datastructures import UploadFile

from app.clipping.settings import ClipSettings
from app.clipping.tools import ClipFailure, probe_duration, run

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
UPLOAD_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
CHUNK_BYTES = 1024 * 1024


def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and (parsed.hostname or "").lower() in YOUTUBE_HOSTS


def download(settings: ClipSettings, url: str, folder: Path) -> Path | ClipFailure:
    # Homebrew installs deno next to yt-dlp, and yt-dlp needs it on PATH for YouTube's JavaScript challenge.
    tool_dir = str(Path(settings.yt_dlp).parent)
    env = {**os.environ, "PATH": os.pathsep.join([tool_dir, os.environ.get("PATH", "")])}
    output = run(
        [
            settings.yt_dlp,
            "--no-playlist",
            "--no-progress",
            "--match-filter", f"duration <= {settings.max_duration_seconds}",
            "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b",
            "--merge-output-format", "mp4",
            "--ffmpeg-location", settings.ffmpeg,
            "-o", str(folder / "source.%(ext)s"),
            "--print", "after_move:filepath",
            url,
        ],
        timeout=1800,
        env=env,
    )
    if isinstance(output, ClipFailure):
        return output
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines or not Path(lines[-1]).is_file():
        minutes = settings.max_duration_seconds // 60
        return ClipFailure(f"The video was not downloaded. It may be longer than {minutes} minutes.")
    return Path(lines[-1])


async def save_upload(upload: UploadFile, folder: Path, max_bytes: int) -> Path | ClipFailure:
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in UPLOAD_EXTENSIONS:
        return ClipFailure(f"Upload a video file ({', '.join(sorted(UPLOAD_EXTENSIONS))}).")
    destination = folder / f"source{extension}"
    written = 0
    with destination.open("wb") as handle:
        while True:
            chunk = await upload.read(CHUNK_BYTES)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                handle.close()
                destination.unlink(missing_ok=True)
                return ClipFailure(f"The upload is larger than {max_bytes // (1024 * 1024)} MB.")
            handle.write(chunk)
    if written == 0:
        destination.unlink(missing_ok=True)
        return ClipFailure("The upload is empty.")
    return destination


def check_duration(settings: ClipSettings, path: Path) -> float | ClipFailure:
    duration = probe_duration(settings, path)
    if isinstance(duration, ClipFailure):
        return duration
    if duration > settings.max_duration_seconds:
        return ClipFailure(f"The video is longer than {settings.max_duration_seconds // 60} minutes.")
    return duration
