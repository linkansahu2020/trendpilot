from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4


@dataclass
class InstagramLogin:
    user_id: str
    access_token: str
    expires_at: datetime


class InstagramSessionStore:
    def __init__(self) -> None:
        self._states: dict[str, datetime] = {}
        self._session: InstagramLogin | None = None
        self._lock = Lock()

    def create_state(self) -> str:
        now = datetime.now(timezone.utc)
        with self._lock:
            expired = [key for key, expires_at in self._states.items() if expires_at <= now]
            for key in expired:
                del self._states[key]
            state = uuid4().hex
            self._states[state] = now + timedelta(minutes=10)
            return state

    def try_consume_state(self, state: str) -> bool:
        with self._lock:
            expires_at = self._states.pop(state, None)
        return expires_at is not None and expires_at > datetime.now(timezone.utc)

    def set_login(self, login: InstagramLogin) -> None:
        with self._lock:
            self._session = login

    def get_valid(self) -> InstagramLogin | None:
        with self._lock:
            if self._session is None or self._session.expires_at <= datetime.now(timezone.utc):
                self._session = None
                return None
            return self._session
