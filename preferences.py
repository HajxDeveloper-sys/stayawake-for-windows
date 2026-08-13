"""Small, dependency-free persistence layer for user preferences.

The repository's ``config.toml`` remains a safe, distributable defaults file.
Personal choices belong in the current user's AppData directory so an update or
packaged build never tries to modify its installation directory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_PREFERENCES: dict[str, Any] = {
    "language": "TR",
    "keep_display": True,
    "keep_system": True,
    "virtual_heartbeat": False,
    "session_preset": "continuous",
    "custom_duration_minutes": 30,
    "geometry": "520x700",
}

VALID_PRESETS = {"continuous", "30", "60", "120", "custom"}


def get_preferences_path(app_data_dir: str | Path | None = None) -> Path:
    """Return the per-user preferences path without creating it."""
    if app_data_dir is not None:
        root = Path(app_data_dir)
    else:
        root = Path(os.environ.get("APPDATA", Path.home() / ".stayawake")) / "StayAwake"
    return root / "preferences.json"


def _valid_geometry(value: Any) -> str:
    if not isinstance(value, str):
        return DEFAULT_PREFERENCES["geometry"]
    width_height = value.lower().split("x", maxsplit=1)
    if len(width_height) != 2:
        return DEFAULT_PREFERENCES["geometry"]
    try:
        width, height = (int(part) for part in width_height)
    except ValueError:
        return DEFAULT_PREFERENCES["geometry"]
    if 460 <= width <= 2000 and 580 <= height <= 1600:
        return f"{width}x{height}"
    return DEFAULT_PREFERENCES["geometry"]


def sanitize_preferences(raw: Any) -> dict[str, Any]:
    """Merge an untrusted preferences file into validated defaults."""
    safe = dict(DEFAULT_PREFERENCES)
    if not isinstance(raw, dict):
        return safe

    language = raw.get("language")
    if isinstance(language, str) and language.upper() in {"TR", "EN"}:
        safe["language"] = language.upper()

    for key in ("keep_display", "keep_system", "virtual_heartbeat"):
        if isinstance(raw.get(key), bool):
            safe[key] = raw[key]

    preset = raw.get("session_preset")
    if isinstance(preset, str) and preset in VALID_PRESETS:
        safe["session_preset"] = preset

    custom_minutes = raw.get("custom_duration_minutes")
    if isinstance(custom_minutes, int) and not isinstance(custom_minutes, bool):
        safe["custom_duration_minutes"] = max(1, min(24 * 60, custom_minutes))

    safe["geometry"] = _valid_geometry(raw.get("geometry"))
    return safe


class PreferencesStore:
    """Load and atomically save application preferences for one user."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else get_preferences_path()

    def load(self) -> dict[str, Any]:
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                return sanitize_preferences(json.load(handle))
        except (OSError, ValueError, TypeError):
            return dict(DEFAULT_PREFERENCES)

    def save(self, preferences: dict[str, Any]) -> bool:
        safe = sanitize_preferences(preferences)
        temp_path = self.path.with_suffix(".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(safe, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
            temp_path.replace(self.path)
            return True
        except OSError:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False
