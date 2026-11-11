from __future__ import annotations

from pathlib import Path

from app.clipping.settings import ClipSettings
from app.clipping.tools import ClipFailure, run
from app.clipping.transcribe import Segment, Word

MAX_WORDS_PER_LINE = 3
MAX_CHARACTERS_PER_LINE = 16
LINE_BREAK_GAP_SECONDS = 0.6
HIGHLIGHT_COLOR = "&H0000E5FF&"

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,2,60,60,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def words_in_range(segments: list[Segment], start: float, end: float) -> list[Word]:
    return [
        Word(start=max(word.start, start) - start, end=min(word.end, end) - start, text=word.text)
        for segment in segments
        for word in segment.words
        if word.text and word.end > start and word.start < end
    ]


def group_lines(words: list[Word]) -> list[list[Word]]:
    lines: list[list[Word]] = []
    for word in words:
        current = lines[-1] if lines else None
        if (
            current is None
            or len(current) >= MAX_WORDS_PER_LINE
            or sum(len(item.text) + 1 for item in current) + len(word.text) > MAX_CHARACTERS_PER_LINE
            or word.start - current[-1].end > LINE_BREAK_GAP_SECONDS
            or current[-1].text[-1:] in {".", "?", "!"}
        ):
            lines.append([word])
        else:
            current.append(word)
    return lines


def ass_time(seconds: float) -> str:
    centiseconds = max(0, int(round(seconds * 100)))
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def ass_text(text: str) -> str:
    return text.replace("\\", "").replace("{", "").replace("}", "").upper()


def build_ass(words: list[Word]) -> str:
    events: list[str] = []
    for line in group_lines(words):
        for position, word in enumerate(line):
            shown_until = line[position + 1].start if position + 1 < len(line) else word.end
            parts = [
                f"{{\\c{HIGHLIGHT_COLOR}}}{ass_text(other.text)}{{\\r}}" if other is word else ass_text(other.text)
                for other in line
            ]
            events.append(
                f"Dialogue: 0,{ass_time(word.start)},{ass_time(max(shown_until, word.start + 0.05))},"
                f"Caption,,0,0,0,,{' '.join(parts)}"
            )
    return ASS_HEADER + "\n".join(events) + "\n"


def render_clip(
    settings: ClipSettings, source: Path, segments: list[Segment], start: float, end: float, index: int, folder: Path
) -> Path | ClipFailure:
    output_path = folder / f"clip-{index}.mp4"
    filters = ["crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'", "scale=1080:1920", "setsar=1"]

    words = words_in_range(segments, start, end)
    subtitles_name = f"clip-{index}.ass"
    if words:
        (folder / subtitles_name).write_text(build_ass(words), encoding="utf-8")
        filters.append(f"subtitles={subtitles_name}")

    output = run(
        [
            settings.ffmpeg, "-y",
            "-ss", f"{start:.2f}", "-i", str(source.resolve()), "-t", f"{end - start:.2f}",
            "-vf", ",".join(filters),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart",
            output_path.name,
        ],
        cwd=folder,
    )
    (folder / subtitles_name).unlink(missing_ok=True)
    if isinstance(output, ClipFailure):
        return output
    return output_path
