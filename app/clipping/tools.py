from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.clipping.settings import ClipSettings


@dataclass
class ClipFailure:
    message: str


def run(
    command: list[str],
    cwd: Path | None = None,
    timeout: float | None = None,
    env: dict[str, str] | None = None,
) -> str | ClipFailure:
    name = Path(command[0]).name
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    except FileNotFoundError:
        return ClipFailure(f"{name} is not installed.")
    except subprocess.TimeoutExpired:
        return ClipFailure(f"{name} took too long and was stopped.")
    if result.returncode != 0:
        return ClipFailure(f"{name} failed: {read_failure(result.stderr) or f'exit code {result.returncode}'}")
    return result.stdout


def read_failure(stderr: str) -> str:
    lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
    errors = [line[len("ERROR:") :].strip() for line in lines if line.startswith("ERROR:")]
    return " ".join(errors or lines[-3:])


def probe_duration(settings: ClipSettings, path: Path) -> float | ClipFailure:
    output = run(
        [settings.ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        timeout=60,
    )
    if isinstance(output, ClipFailure):
        return ClipFailure("The file could not be read as a video.")
    try:
        duration = float(json.loads(output)["format"]["duration"])
    except (ValueError, KeyError, TypeError):
        return ClipFailure("The video duration could not be read.")
    if duration <= 0:
        return ClipFailure("The video is empty.")
    return duration
