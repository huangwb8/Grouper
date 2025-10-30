from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional


def _detect_base_dir() -> Path:
    """Detect base directory for assets/settings.

    - If running under PyInstaller, use the temporary extraction dir.
    - Otherwise, use repository root (two levels up from this file).
    """
    base = None
    try:
        # type: ignore[attr-defined]
        import sys as _sys

        if hasattr(_sys, "_MEIPASS"):
            base = Path(getattr(_sys, "_MEIPASS"))
    except Exception:
        base = None
    if not base:
        base = Path(__file__).resolve().parents[2]
    return base


APP_DIR = _detect_base_dir()


def _user_data_dir() -> Path:
    """Return a user-writable data directory for settings at runtime.

    - Windows: %APPDATA%/Grouper
    - macOS:   ~/Library/Application Support/Grouper
    - Linux:   $XDG_CONFIG_HOME/grouper or ~/.config/grouper
    """
    plat = os.name
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "Grouper"
        # Fallback to Roaming
        return Path.home() / "AppData" / "Roaming" / "Grouper"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Grouper"
    else:
        base = os.environ.get("XDG_CONFIG_HOME")
        if base:
            return Path(base) / "grouper"
        return Path.home() / ".config" / "grouper"


# In packaged mode, write settings to a user-writable location.
# In source mode, keep everything under the project for convenience.
import sys as _sys  # local import to avoid shadowing above try block


def _is_packaged() -> bool:
    try:
        return hasattr(_sys, "_MEIPASS")
    except Exception:
        return False


if _is_packaged():
    RUNTIME_DIR = _user_data_dir()
else:
    RUNTIME_DIR = APP_DIR

# Required subdir as per prompt
X86_64_DIR = RUNTIME_DIR / "x86_64"
ASSETS_DIR = X86_64_DIR / "assets"
SETTINGS_FILE = X86_64_DIR / "settings.json"


if _is_packaged():
    # In packaged mode, assets live under <runtime>/assets
    ASSETS_DIR = APP_DIR / "assets"  # type: ignore[assignment]
else:
    # In source mode, use x86_64/assets
    ASSETS_DIR = (RUNTIME_DIR / "x86_64" / "assets")  # type: ignore[assignment]


def ensure_runtime_dirs() -> None:
    X86_64_DIR.mkdir(parents=True, exist_ok=True)
    # Only ensure source assets dir; in packaged mode it's read-only
    if not _is_packaged():
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    save_dir: str = "."
    per_teacher: int = 3
    students_text: str = ""
    teachers_text: str = ""
    geometry: Optional[str] = None  # Qt geometry serialized as hex string
    font_size: int = 10

    @classmethod
    def load(cls) -> "Settings":
        ensure_runtime_dirs()
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                return cls(**data)
            except Exception:
                pass
        # default save dir = current working directory
        return cls(save_dir=os.getcwd())

    def save(self) -> None:
        ensure_runtime_dirs()
        SETTINGS_FILE.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
