from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.env import load_env_file, repo_root

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_WHISPER_MODEL = "small"
DEFAULT_WORK_DIR = "data/clips"
DEFAULT_MAX_DURATION_MINUTES = 60
DEFAULT_MAX_UPLOAD_MB = 2048
HOMEBREW_YT_DLP = "/opt/homebrew/bin/yt-dlp"


@dataclass
class ClipSettings:
    gemini_api_key: str
    gemini_model: str
    whisper_model: str
    work_dir: Path
    max_duration_seconds: int
    max_upload_bytes: int
    allow_urls: bool
    ffmpeg: str
    ffprobe: str
    yt_dlp: str


def _read_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, "").strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _find_tool(folder: str, name: str) -> str:
    if folder:
        candidate = Path(folder) / name
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name) or name


def _find_yt_dlp() -> str:
    configured = os.environ.get("Clips__YtDlpPath", "").strip()
    if configured:
        return configured
    # A server started from an IDE may not have Homebrew on PATH.
    return shutil.which("yt-dlp") or HOMEBREW_YT_DLP


def load_clip_settings() -> ClipSettings:
    load_env_file()
    work_dir = Path(os.environ.get("Clips__WorkDir", DEFAULT_WORK_DIR).strip() or DEFAULT_WORK_DIR)
    if not work_dir.is_absolute():
        work_dir = repo_root() / work_dir
    ffmpeg_dir = os.environ.get("Clips__FfmpegDir", "").strip()
    return ClipSettings(
        gemini_api_key=os.environ.get("Gemini__ApiKey", "").strip(),
        gemini_model=os.environ.get("Gemini__Model", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL,
        whisper_model=os.environ.get("Whisper__Model", DEFAULT_WHISPER_MODEL).strip() or DEFAULT_WHISPER_MODEL,
        work_dir=work_dir,
        max_duration_seconds=_read_int("Clips__MaxDurationMinutes", DEFAULT_MAX_DURATION_MINUTES) * 60,
        max_upload_bytes=_read_int("Clips__MaxUploadMb", DEFAULT_MAX_UPLOAD_MB) * 1024 * 1024,
        allow_urls=os.environ.get("Clips__AllowUrls", "true").strip().lower() not in {"false", "0", "no"},
        ffmpeg=_find_tool(ffmpeg_dir, "ffmpeg"),
        ffprobe=_find_tool(ffmpeg_dir, "ffprobe"),
        yt_dlp=_find_yt_dlp(),
    )


def missing_clip_configuration_message(settings: ClipSettings) -> str | None:
    if not settings.gemini_api_key:
        return "Gemini API key is not configured. Set Gemini__ApiKey to a key from https://aistudio.google.com/apikey."
    if not Path(settings.ffmpeg).is_file() or not Path(settings.ffprobe).is_file():
        return "ffmpeg and ffprobe were not found. Install ffmpeg-full and set Clips__FfmpegDir."
    return None


def missing_url_configuration_message(settings: ClipSettings) -> str | None:
    if not Path(settings.yt_dlp).is_file():
        return "yt-dlp was not found. Install it with `brew install yt-dlp`, or set Clips__YtDlpPath."
    return None
