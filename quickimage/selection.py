"""grab whatever text is selected in the window that currently has focus

windows has no api for "just give me the selection", so the usual hack is to fire
Ctrl+C at the focused window and read the clipboard back. two things make that
flaky and this module deals with both:

* the hotkey is still holding modifiers down. dont release them and the fake
  Ctrl+C shows up as Ctrl+Alt+Shift+C and the copy quietly does nothing
* chromium apps (discord, slack, browsers) answer Ctrl+C a beat late and every
  now and then drop the first one, so we poll the clipboard and retry
"""

import time

import keyboard
import win32clipboard as wc

from . import winclip

# every modifier we might be holding. any of these left physically down would
# wreck the synthetic Ctrl+C (the trigger key gets added on top per-call)
_MODIFIERS = (
    "ctrl", "left ctrl", "right ctrl",
    "alt", "left alt", "right alt", "alt gr",
    "shift", "left shift", "right shift",
    "windows", "left windows", "right windows",
)


def _release_all(hotkey: str = "") -> None:
    keys = list(_MODIFIERS)
    # the trigger key (the "i" in alt+i) is still held down when the hook fires
    keys += [part.strip() for part in hotkey.split("+") if part.strip()]
    for key in keys:
        try:
            keyboard.release(key)
        except Exception:
            pass


def _send_copy() -> None:
    """explicit press/release works way better than keyboard.send() inside electron apps"""
    keyboard.press("ctrl")
    keyboard.press("c")
    time.sleep(0.03)
    keyboard.release("c")
    keyboard.release("ctrl")


def get_selected_text(hotkey: str = "", timeout: float = 1.6,
                      attempts: int = 3) -> str:
    """return the current selection, or "" if nothing got copied in time"""
    _release_all(hotkey)
    # let the modifier key-ups actually land before the app sees our Ctrl+C,
    # otherwise as far as the app knows Alt is still down
    time.sleep(0.06)

    deadline = time.time() + timeout
    per_attempt = timeout / attempts

    for _ in range(attempts):
        before = wc.GetClipboardSequenceNumber()
        _send_copy()

        stop = min(time.time() + per_attempt, deadline)
        while time.time() < stop:
            time.sleep(0.03)
            if wc.GetClipboardSequenceNumber() != before:
                # the app might push its formats in stages, so let it settle a bit
                # then read. empty read means it copied something non-text, fall
                # through and give it another go
                time.sleep(0.04)
                try:
                    text = winclip.get_text().strip()
                except RuntimeError:
                    text = ""
                if text:
                    return text
                break
        if time.time() >= deadline:
            break

    return ""
