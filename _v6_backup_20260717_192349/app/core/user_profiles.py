"""Display names and logins without changing the existing users table."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel


class UserProfile(BaseModel):
    username: str
    full_name: str


PROFILES_PATH = Path.cwd() / "autocrm_user_profiles.json"
USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")


def normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not USERNAME_RE.fullmatch(username):
        raise ValueError(
            "Логин: 3–32 символа, только латинские буквы, цифры, точка, _ и -"
        )
    return username


def load_profiles() -> dict[str, UserProfile]:
    if not PROFILES_PATH.exists():
        return {}
    try:
        raw = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        return {
            str(key): UserProfile.model_validate(value)
            for key, value in raw.items()
        }
    except (OSError, ValueError, TypeError):
        return {}


def save_profiles(profiles: dict[str, UserProfile]) -> None:
    temp = PROFILES_PATH.with_suffix(".json.tmp")
    temp.write_text(
        json.dumps(
            {key: value.model_dump() for key, value in profiles.items()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temp.replace(PROFILES_PATH)


def fallback_username(email: str) -> str:
    return email.split("@", 1)[0]


def profile_for(user_id: int, email: str, role: str) -> UserProfile:
    stored = load_profiles().get(str(user_id))
    if stored:
        return stored
    username = fallback_username(email)
    full_name = "Директор" if role == "admin" else f"Менеджер #{user_id}"
    return UserProfile(username=username, full_name=full_name)


def set_profile(user_id: int, username: str, full_name: str) -> UserProfile:
    profiles = load_profiles()
    profile = UserProfile(
        username=normalize_username(username),
        full_name=full_name.strip(),
    )
    if len(profile.full_name) < 2:
        raise ValueError("Укажите фамилию и имя менеджера")
    profiles[str(user_id)] = profile
    save_profiles(profiles)
    return profile
