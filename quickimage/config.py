"""settings live as json in the APPDATA folder, loaded once at startup"""

import json
import os
import sys
import threading

APP_NAME = "QuickImage"
ICON_FILE = "Icon.ico"


def icon_path() -> str | None:
    """where the app icon lives - works both in dev and inside a pyinstaller build

    pyinstaller unpacks bundled data into sys._MEIPASS, otherwise the ico just
    sits in the project root one level up from this package
    """
    candidates = []
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        candidates.append(os.path.join(bundle, ICON_FILE))
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(root, ICON_FILE))
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

DEFAULTS = {
    "hotkey": "alt+i",
    "provider": "auto",     # auto / duckduckgo / openverse
    "safe_search": "off",       # off, medium or high
    "image_size": "large",      # icon..huge, or any to not filter
    "max_pixels": 2000,         # shrink the longest edge before copying, 0 leaves it alone
    "copy_url_too": True,       # drop the source url on the clipboard as text too
    "restore_clipboard": False, # put the old clipboard back if the search dies
    "notifications": True,
    "start_minimized": True,
}


def config_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, APP_NAME)


def config_path() -> str:
    return os.path.join(config_dir(), "config.json")


class Config:
    """dict-ish config that saves atomically. read/written from a couple threads so theres a lock"""

    def __init__(self):
        self._lock = threading.Lock()
        self._data = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            with open(config_path(), "r", encoding="utf-8") as fh:
                stored = json.load(fh)
        except (OSError, ValueError):
            stored = {}
        with self._lock:
            self._data = dict(DEFAULTS)
            for key, value in stored.items():
                if key in DEFAULTS:
                    self._data[key] = value

    def save(self) -> None:
        os.makedirs(config_dir(), exist_ok=True)
        with self._lock:
            snapshot = dict(self._data)
        tmp = config_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2)
        os.replace(tmp, config_path())

    def __getitem__(self, key):
        with self._lock:
            return self._data[key]

    def __setitem__(self, key, value):
        with self._lock:
            self._data[key] = value

    def get(self, key, default=None):
        with self._lock:
            return self._data.get(key, default)

    def update(self, values: dict) -> None:
        with self._lock:
            self._data.update(values)

