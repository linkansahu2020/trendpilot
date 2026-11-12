from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError

from app.clipping.gemini import GeminiFailure, generate_json
from app.clipping.settings import ClipSettings
from app.clipping.transcribe import Segment

MIN_CLIP_SECONDS = 15.0
MAX_CLIP_SECONDS = 60.0
SHORTEST_KEPT_SECONDS = 10.0
MAX_CLIPS = 8

PROMPT = """You are a short-form video editor who finds the moments most likely to go viral on Instagram Reels, YouTube Shorts, and TikTok.

Watch the attached video and read its transcript. Each transcript line is "[start-end] text" in seconds.

Pick between 3 and {max_clips} clips. Each clip must:
- Be between {min_seconds:.0f} and {max_seconds:.0f} seconds long.
- Open with a strong hook in the first 3 seconds: a bold claim, a question, a surprise, or a striking visual.
- Make sense on its own without the rest of the video, and end on a payoff, punchline, or clear takeaway.
- Start and end on sentence boundaries from the transcript when there is speech.
- Not overlap any other clip.

Prefer emotional peaks, strong opinions, useful tips, funny moments, and visual moments such as reactions or demos.

For each clip return:
- start and end in seconds from the start of the video.
- hook: the first line or visual that grabs attention.
- title: a short on-screen title, at most 8 words.
- caption: a social media caption of 1 to 2 sentences.
- hashtags: 3 to 6 hashtags without the # sign.
- score: 1 to 100, how likely the clip is to go viral.

The video is {duration:.0f} seconds long.

Transcript:
{transcript}"""


class ClipCandidate(BaseModel):
    start: float
    end: float
    hook: str
    title: str
    caption: str
    hashtags: list[str]
    score: int


class ClipCandidates(BaseModel):
    clips: list[ClipCandidate]


@dataclass
class Moment:
    start: float
    end: float
    hook: str
    title: str
    caption: str
    hashtags: list[str]
    score: int


def format_transcript(segments: list[Segment]) -> str:
    if not segments:
        return "(no speech detected)"
    return "\n".join(f"[{segment.start:.1f}-{segment.end:.1f}] {segment.text}" for segment in segments)


def select_moments(
    settings: ClipSettings, proxy: Path, segments: list[Segment], duration: float
) -> list[Moment] | GeminiFailure:
    prompt = PROMPT.format(
        max_clips=MAX_CLIPS,
        min_seconds=MIN_CLIP_SECONDS,
        max_seconds=MAX_CLIP_SECONDS,
        duration=duration,
        transcript=format_transcript(segments),
    )
    answer = generate_json(settings, proxy, prompt, ClipCandidates)
    if isinstance(answer, GeminiFailure):
        return answer
    try:
        candidates = ClipCandidates.model_validate_json(answer).clips
    except ValidationError:
        return GeminiFailure("Gemini returned clips in an unexpected format.")

    moments: list[Moment] = []
    for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
        bounds = snap(candidate.start, candidate.end, segments, duration)
        if bounds is None:
            continue
        start, end = bounds
        if any(start < kept.end and kept.start < end for kept in moments):
            continue
        moments.append(
            Moment(
                start=start,
                end=end,
                hook=candidate.hook.strip(),
                title=candidate.title.strip(),
                caption=candidate.caption.strip(),
                hashtags=read_hashtags(candidate.hashtags),
                score=max(1, min(100, candidate.score)),
            )
        )
        if len(moments) == MAX_CLIPS:
            break
    if not moments:
        return GeminiFailure("Gemini did not find any usable clips in this video.")
    return moments


def read_hashtags(raw_tags: list[str]) -> list[str]:
    tags: list[str] = []
    for raw in raw_tags:
        for tag in re.split(r"[#\s,]+", raw):
            if tag and tag not in tags:
                tags.append(tag)
    return tags


def snap(start: float, end: float, segments: list[Segment], duration: float) -> tuple[float, float] | None:
    start = max(0.0, min(start, duration))
    end = max(0.0, min(end, duration))
    if end <= start:
        return None

    if segments:
        starts = [segment.start for segment in segments if segment.start <= start + 0.5]
        start = starts[-1] if starts else segments[0].start
        ends = [segment.end for segment in segments if segment.end >= end - 0.5]
        end = ends[0] if ends else segments[-1].end

    if end - start > MAX_CLIP_SECONDS:
        fitting = [segment.end for segment in segments if start + MIN_CLIP_SECONDS <= segment.end <= start + MAX_CLIP_SECONDS]
        end = fitting[-1] if fitting else start + MAX_CLIP_SECONDS

    end = min(end, duration)
    if end - start < SHORTEST_KEPT_SECONDS:
        return None
    return round(start, 2), round(end, 2)
