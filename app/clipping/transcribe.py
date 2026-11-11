from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from faster_whisper import WhisperModel

from app.clipping.settings import ClipSettings
from app.clipping.tools import ClipFailure, run

_models: dict[str, WhisperModel] = {}
_models_lock = Lock()


@dataclass
class Word:
    start: float
    end: float
    text: str


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word]


def _get_model(name: str) -> WhisperModel:
    with _models_lock:
        model = _models.get(name)
        if model is None:
            model = WhisperModel(name, device="cpu", compute_type="int8")
            _models[name] = model
        return model


def transcribe(settings: ClipSettings, video: Path, folder: Path) -> list[Segment] | ClipFailure:
    audio = folder / "audio.wav"
    output = run([settings.ffmpeg, "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    if isinstance(output, ClipFailure):
        return output

    try:
        model = _get_model(settings.whisper_model)
        raw_segments, _ = model.transcribe(str(audio), word_timestamps=True, vad_filter=True)
        segments = [
            Segment(
                start=raw.start,
                end=raw.end,
                text=raw.text.strip(),
                words=[Word(start=word.start, end=word.end, text=word.word.strip()) for word in raw.words or []],
            )
            for raw in raw_segments
        ]
    except Exception as error:
        return ClipFailure(f"Transcription failed: {error}")
    finally:
        audio.unlink(missing_ok=True)
    return [segment for segment in segments if segment.text]
