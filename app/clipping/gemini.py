from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google import genai
from google.genai import errors, types

from app.clipping.settings import ClipSettings
from app.clipping.tools import ClipFailure, run

FILE_PROCESSING_TIMEOUT_SECONDS = 600
OVERLOADED_RETRY_DELAYS_SECONDS = (15, 30, 60)


@dataclass
class GeminiFailure:
    message: str


def encode_proxy(settings: ClipSettings, source: Path, destination: Path) -> Path | ClipFailure:
    output = run(
        [
            settings.ffmpeg, "-y", "-i", str(source),
            "-vf", "fps=1,scale=-2:360",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "32",
            "-c:a", "aac", "-b:a", "48k", "-ac", "1",
            str(destination),
        ]
    )
    if isinstance(output, ClipFailure):
        return output
    return destination


def generate_json(settings: ClipSettings, video: Path, prompt: str, schema: Any) -> str | GeminiFailure:
    client = genai.Client(api_key=settings.gemini_api_key)
    uploaded: types.File | None = None
    try:
        uploaded = client.files.upload(file=str(video), config=types.UploadFileConfig(mime_type="video/mp4"))
        deadline = time.monotonic() + FILE_PROCESSING_TIMEOUT_SECONDS
        while uploaded.state == types.FileState.PROCESSING:
            if time.monotonic() > deadline:
                return GeminiFailure("Gemini took too long to process the video.")
            time.sleep(3)
            uploaded = client.files.get(name=uploaded.name)
        if uploaded.state != types.FileState.ACTIVE:
            return GeminiFailure("Gemini could not process the video.")

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.4,
        )
        for delay in OVERLOADED_RETRY_DELAYS_SECONDS:
            try:
                response = client.models.generate_content(
                    model=settings.gemini_model, contents=[uploaded, prompt], config=config
                )
                break
            except errors.APIError as error:
                if error.code != 503:
                    raise
                time.sleep(delay)
        else:
            response = client.models.generate_content(
                model=settings.gemini_model, contents=[uploaded, prompt], config=config
            )
        if not response.text:
            return GeminiFailure("Gemini returned an empty answer.")
        return response.text
    except errors.APIError as error:
        return GeminiFailure(read_error(error))
    finally:
        if uploaded is not None and uploaded.name:
            try:
                client.files.delete(name=uploaded.name)
            except errors.APIError:
                pass


def read_error(error: errors.APIError) -> str:
    if error.code == 429:
        return "Gemini rate limit reached. The free tier allows a few requests per minute and per day; try again later."
    if error.code in (401, 403) or (error.code == 400 and "API key" in (error.message or "")):
        return "Gemini rejected the API key. Check Gemini__ApiKey."
    if error.code == 404:
        return f"The Gemini model is not available: {error.message or 'not found'} Check Gemini__Model."
    if error.code == 503:
        return "Gemini is overloaded right now. Try again in a few minutes."
    return f"Gemini request failed with status {error.code}: {error.message or 'no details'}"
