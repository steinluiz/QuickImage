"""clipboard helpers - text in and out, plus images shoved in as CF_DIB + PNG"""

import io
import time

import win32clipboard as wc
import win32con
from PIL import Image

CF_PNG = wc.RegisterClipboardFormat("PNG")


def _open(retries: int = 10, delay: float = 0.05):
    """clipboard is a single shared thing, some other app might be holding it for a sec"""
    last = None
    for _ in range(retries):
        try:
            wc.OpenClipboard()
            return
        except Exception as exc:  # usually a pywintypes.error
            last = exc
            time.sleep(delay)
    raise RuntimeError(f"could not open clipboard: {last}")


def get_text() -> str:
    _open()
    try:
        if wc.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            return wc.GetClipboardData(win32con.CF_UNICODETEXT) or ""
        return ""
    finally:
        wc.CloseClipboard()


def set_text(text: str) -> None:
    _open()
    try:
        wc.EmptyClipboard()
        wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        wc.CloseClipboard()


def _to_dib(image: Image.Image) -> bytes:
    """CF_DIB is basically a BMP with the 14 byte file header chopped off"""
    rgb = image.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, "BMP")
    return buf.getvalue()[14:]


def _to_png(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, "PNG")
    return buf.getvalue()


def set_image(image: Image.Image, url: str | None = None) -> None:
    """put the image on the clipboard in every format a paste target might ask for

    CF_DIB covers Word/Paint/Office, PNG keeps transparency for Chrome/Discord/Slack
    and the optional text is just the source url for plain-text spots
    """
    dib = _to_dib(image)
    png = _to_png(image)
    _open()
    try:
        wc.EmptyClipboard()
        wc.SetClipboardData(win32con.CF_DIB, dib)
        wc.SetClipboardData(CF_PNG, png)
        if url:
            wc.SetClipboardData(win32con.CF_UNICODETEXT, url)
    finally:
        wc.CloseClipboard()
