"""colors, fonts and the bit of win32 polish every widget shares

window is dark slate not pure black, and amber is the only accent - it reads like
an indicator lamp which is pretty much what the hotkey status is
"""

import ctypes
import tkinter.font as tkfont

# --- palette
INK = "#14161c"          # window ground
SURFACE = "#1c1f28"      # cards
SURFACE_HI = "#242835"   # hover / raised
EDGE = "#2c3242"         # hairlines
EDGE_HI = "#3b4356"      # same but on hover

TEXT = "#e7e9ef"
MUTED = "#8b91a3"
FAINT = "#5d6478"

AMBER = "#f0b23c"        # armed, accents, whatever needs to pop
AMBER_SOFT = "#4a3a18"   # amber dimmed down to card level
AMBER_DEEP = "#a8761f"
RED = "#e2585b"
GREEN = "#63c08a"

# --- type
_DISPLAY = ["Segoe UI Variable Display", "Segoe UI Semibold", "Segoe UI", "Arial"]
_BODY = ["Segoe UI Variable Text", "Segoe UI", "Arial"]
_MONO = ["Cascadia Mono", "Consolas", "Courier New"]

_cache: dict[str, str] = {}


def _pick(candidates: list[str], key: str) -> str:
    if key not in _cache:
        available = {name.lower() for name in tkfont.families()}
        _cache[key] = next(
            (name for name in candidates if name.lower() in available), candidates[-1]
        )
    return _cache[key]


def display(size: int, weight: str = "normal") -> tuple:
    return (_pick(_DISPLAY, "display"), size, weight)


def body(size: int = 10, weight: str = "normal") -> tuple:
    return (_pick(_BODY, "body"), size, weight)


def mono(size: int = 10, weight: str = "normal") -> tuple:
    return (_pick(_MONO, "mono"), size, weight)


# --- win32 polish


def dark_titlebar(window) -> None:
    """ask DWM for the dark title bar so the frame matches the content"""
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        flag = ctypes.c_int(1)
        for attribute in (20, 19):  # 20 on win10 2004+, 19 on the older builds
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(flag), ctypes.sizeof(flag)
            ) == 0:
                break
    except Exception:
        pass


def round_rect(canvas, x0, y0, x1, y1, radius, **kwargs):
    """canvas cant do rounded rects so a smoothed polygon fakes one, usual trick"""
    radius = min(radius, abs(x1 - x0) / 2, abs(y1 - y0) / 2)
    points = [
        x0 + radius, y0, x1 - radius, y0, x1, y0, x1, y0 + radius,
        x1, y1 - radius, x1, y1, x1 - radius, y1, x0 + radius, y1,
        x0, y1, x0, y1 - radius, x0, y0 + radius, x0, y0,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=32, **kwargs)


def blend(color_a: str, color_b: str, t: float) -> str:
    """mix two #rrggbb colors, used for hovers and the animation frames"""
    a = tuple(int(color_a[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(color_b[i:i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(round(x + (y - x) * t) for x, y in zip(a, b))
    return "#%02x%02x%02x" % mixed
