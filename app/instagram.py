from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

import httpx

from app.session import InstagramLogin

PROFILE_FIELDS = "id,username,name,biography,website,followers_count,follows_count,media_count,profile_picture_url"
MEDIA_FIELDS = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count"
DEFAULT_REDIRECT_URI = "https://localhost:7061/instagram/callback"
DEFAULT_GRAPH_VERSION = "v26.0"
_SECRET_PATTERN = re.compile(r"(access_token|client_secret)=[^&\s\"]+", re.IGNORECASE)


@dataclass
class InstagramSettings:
    app_id: str
    app_secret: str
    redirect_uri: str
    graph_version: str


@dataclass
class InstagramFailure:
    status_code: int
    message: str


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return here.parents[1]


def _load_env_file() -> None:
    path = _repo_root() / ".env"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, separator, value = line.partition("=")
        if not separator:
            continue
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


def load_settings() -> InstagramSettings:
    _load_env_file()
    return InstagramSettings(
        app_id=os.environ.get("Instagram__AppId", "").strip(),
        app_secret=os.environ.get("Instagram__AppSecret", "").strip(),
        redirect_uri=os.environ.get("Instagram__RedirectUri", DEFAULT_REDIRECT_URI).strip(),
        graph_version=os.environ.get("Instagram__GraphVersion", DEFAULT_GRAPH_VERSION).strip().strip("/"),
    )


def missing_configuration_message(settings: InstagramSettings) -> str | None:
    if not settings.app_id or not settings.app_secret:
        return "Instagram app id and app secret are not configured. Set Instagram__AppId and Instagram__AppSecret."
    if not settings.redirect_uri:
        return "Instagram:RedirectUri is not configured."
    if not settings.graph_version:
        return "Instagram:GraphVersion is not configured."
    return None


def build_authorize_url(settings: InstagramSettings, state: str) -> str:
    query = urlencode(
        {
            "client_id": settings.app_id,
            "redirect_uri": settings.redirect_uri,
            "response_type": "code",
            "scope": "instagram_business_basic",
            "state": state,
        }
    )
    return f"https://www.instagram.com/oauth/authorize?{query}"


async def exchange_code(settings: InstagramSettings, code: str) -> InstagramLogin | InstagramFailure:
    if code.endswith("#_"):
        code = code[:-2]

    async with httpx.AsyncClient(timeout=30) as client:
        token_response = await client.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": settings.app_id,
                "client_secret": settings.app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": settings.redirect_uri,
                "code": code,
            },
        )
        token_body = token_response.text
        if token_response.is_error:
            message, graph_code = read_error(token_body, token_response.status_code)
            return InstagramFailure(map_status(token_response.status_code, graph_code), message)

        parsed = read_short_lived_token(token_body)
        if parsed is None:
            return InstagramFailure(502, "Instagram token response did not include a user.")
        user_id, short_lived_token = parsed

        long_lived_query = urlencode(
            {
                "grant_type": "ig_exchange_token",
                "client_secret": settings.app_secret,
                "access_token": short_lived_token,
            }
        )
        long_lived_response = await client.get(f"https://graph.instagram.com/access_token?{long_lived_query}")
        long_lived_body = long_lived_response.text
        if long_lived_response.is_error:
            message, graph_code = read_error(long_lived_body, long_lived_response.status_code)
            return InstagramFailure(map_status(long_lived_response.status_code, graph_code), message)

        long_lived = read_long_lived_token(long_lived_body)
        if long_lived is None:
            return InstagramFailure(502, "Instagram did not return a long-lived token.")
        access_token, expires_in = long_lived

    return InstagramLogin(
        user_id=user_id,
        access_token=access_token,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    )


async def get_account(settings: InstagramSettings, user_id: str, access_token: str) -> dict[str, Any] | InstagramFailure:
    version = settings.graph_version or DEFAULT_GRAPH_VERSION
    escaped_user_id = quote(user_id, safe="")
    escaped_token = quote(access_token, safe="")
    async with httpx.AsyncClient(timeout=30) as client:
        profile_url = (
            f"https://graph.instagram.com/{version}/{escaped_user_id}"
            f"?fields={PROFILE_FIELDS}&access_token={escaped_token}"
        )
        profile_response = await client.get(profile_url)
        if profile_response.is_error:
            message, graph_code = read_error(profile_response.text, profile_response.status_code)
            return InstagramFailure(map_status(profile_response.status_code, graph_code), message)

        media_url = (
            f"https://graph.instagram.com/{version}/{escaped_user_id}/media"
            f"?fields={MEDIA_FIELDS}&limit=25&access_token={escaped_token}"
        )
        media_response = await client.get(media_url)
        if media_response.is_error:
            message, graph_code = read_error(media_response.text, media_response.status_code)
            return InstagramFailure(map_status(media_response.status_code, graph_code), message)

    profile = read_profile(profile_response.json(), user_id)
    media, next_cursor = read_media(media_response.json())
    return {"profile": profile, "media": media, "nextCursor": next_cursor}


def read_short_lived_token(body: str) -> tuple[str, str] | None:
    try:
        payload = json.loads(body)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    if "data" in payload:
        data = payload["data"]
        if not isinstance(data, list) or not data:
            return None
        return read_token_fields(data[0])
    return read_token_fields(payload)


def read_token_fields(item: Any) -> tuple[str, str] | None:
    if not isinstance(item, dict):
        return None
    access_token = item.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        return None
    if "user_id" not in item:
        return None
    user_id = read_id(item["user_id"])
    if not user_id:
        return None
    return user_id, access_token


def read_long_lived_token(body: str) -> tuple[str, int] | None:
    try:
        payload = json.loads(body)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    access_token = payload.get("access_token")
    expires_in = payload.get("expires_in")
    if not isinstance(access_token, str) or not access_token:
        return None
    if isinstance(expires_in, bool) or not isinstance(expires_in, int) or expires_in <= 0:
        return None
    return access_token, expires_in


def read_profile(payload: dict[str, Any], fallback_user_id: str) -> dict[str, Any]:
    return {
        "id": read_id(payload.get("id")) or fallback_user_id,
        "username": read_string(payload, "username"),
        "name": read_string(payload, "name"),
        "biography": read_string(payload, "biography"),
        "website": read_string(payload, "website"),
        "followersCount": read_int(payload, "followers_count"),
        "followsCount": read_int(payload, "follows_count"),
        "mediaCount": read_int(payload, "media_count"),
        "profilePictureUrl": read_string(payload, "profile_picture_url"),
    }


def read_media(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    media: list[dict[str, Any]] = []
    for item in payload.get("data") or []:
        if not isinstance(item, dict):
            continue
        media_id = read_id(item.get("id"))
        if not media_id:
            continue
        timestamp = item.get("timestamp")
        media.append(
            {
                "id": media_id,
                "caption": read_string(item, "caption"),
                "mediaType": read_string(item, "media_type"),
                "mediaUrl": read_string(item, "media_url"),
                "permalink": read_string(item, "permalink"),
                "timestamp": timestamp if isinstance(timestamp, str) else None,
                "likeCount": read_int(item, "like_count"),
                "commentsCount": read_int(item, "comments_count"),
            }
        )
    next_cursor = None
    paging = payload.get("paging")
    if isinstance(paging, dict):
        cursors = paging.get("cursors")
        if isinstance(cursors, dict) and isinstance(cursors.get("after"), str):
            next_cursor = cursors["after"]
    return media, next_cursor


def read_error(body: str, status: int) -> tuple[str, int | None]:
    try:
        payload = json.loads(body)
    except ValueError:
        return f"Instagram request failed with status {status}.", None
    if not isinstance(payload, dict):
        return f"Instagram request failed with status {status}.", None
    error = payload.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        graph_code = code if isinstance(code, int) and not isinstance(code, bool) else None
        return redact(error.get("message") if isinstance(error.get("message"), str) else None), graph_code
    if isinstance(error, str):
        description = payload.get("error_description")
        return redact(description if isinstance(description, str) else error), None
    if isinstance(payload.get("error_message"), str):
        return redact(payload["error_message"]), None
    return f"Instagram request failed with status {status}.", None


def map_status(status: int, graph_code: int | None) -> int:
    if status in (401, 403):
        return 403
    if graph_code in (10, 102, 190, 200):
        return 403
    if 400 <= status <= 499:
        return status
    return 502


def read_id(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    return ""


def read_string(payload: dict[str, Any], name: str) -> str | None:
    value = payload.get(name)
    return value if isinstance(value, str) else None


def read_int(payload: dict[str, Any], name: str) -> int | None:
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def redact(message: str | None) -> str:
    if message is None or not message.strip():
        return "Instagram request failed."
    return _SECRET_PATTERN.sub(r"\1=REDACTED", message)
