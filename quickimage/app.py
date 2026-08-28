"""the core service - owns the hotkey, the worker, the tray icon and notifications"""

import threading
import traceback

import keyboard
import pystray
from PIL import Image, ImageDraw

from . import search, selection, winclip
from .config import APP_NAME, Config, icon_path


def make_tray_image() -> Image.Image:
    """the tray icon - load Icon.ico if its around, else fall back to a drawn one"""
    path = icon_path()
    if path:
        try:
            return Image.open(path)
        except Exception:
            pass  # busted ico, drop through to the drawn fallback

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    body = (46, 125, 233, 255)
    draw.rounded_rectangle((4, 8, 60, 56), radius=10, fill=body)
    draw.rounded_rectangle((12, 18, 52, 48), radius=5, fill=(255, 255, 255, 255))
    draw.ellipse((17, 23, 27, 33), fill=body)
    draw.polygon([(14, 46), (28, 30), (38, 40), (46, 32), (50, 46)], fill=body)
    return img


class QuickImageApp:
    """glue layer. no UI of its own, the gui pokes it through callbacks"""

    def __init__(self, config: Config):
        self.config = config
        self.icon: pystray.Icon | None = None
        self._hotkey_handle = None
        self._busy = threading.Lock()
        self._status = "Idle"
        # main.py sets these so tray menu clicks can hop back onto the Tk thread
        self.on_open_settings = lambda: None
        self.on_quit = lambda: None

    # ---------------------------------------------------------------- hotkey

    def register_hotkey(self, hotkey: str | None = None) -> tuple[bool, str]:
        """(re)bind the global hotkey, returns (ok, message)"""
        hotkey = hotkey or self.config["hotkey"]
        self.unregister_hotkey()
        try:
            # suppress=True stops the combo reaching the focused app, so an alt-based
            # hotkey cant trip the windows menu bar or an electron app's alt handling
            # and yank the selection out from under us before we copy it
            self._hotkey_handle = keyboard.add_hotkey(
                hotkey, self._on_hotkey, suppress=True, trigger_on_release=False
            )
        except Exception as exc:
            self._hotkey_handle = None
            return False, f"Could not register {hotkey!r}: {exc}"
        return True, f"Listening for {hotkey}"

    def unregister_hotkey(self) -> None:
        if self._hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self._hotkey_handle)
            except (KeyError, ValueError):
                pass
            self._hotkey_handle = None

    def _on_hotkey(self) -> None:
        # this runs on the keyboard hook thread, so hand off fast and never block it
        if self._busy.locked():
            self.notify("Still working on the previous search.")
            return
        threading.Thread(target=self._run_capture, daemon=True).start()

    # ---------------------------------------------------------------- worker

    def _run_capture(self) -> None:
        with self._busy:
            try:
                self._capture()
            except search.SearchError as exc:
                self.set_status(str(exc))
                self.notify(str(exc))
            except Exception as exc:
                traceback.print_exc()
                self.set_status(f"Error: {exc}")
                self.notify(f"Unexpected error: {exc}")

    def _capture(self) -> None:
        original = ""
        if self.config["restore_clipboard"]:
            try:
                original = winclip.get_text()
            except RuntimeError:
                original = ""

        query = selection.get_selected_text(self.config["hotkey"])
        if not query:
            raise search.SearchError(
                "No text selected. Highlight some text first, then press the hotkey."
            )
        if len(query) > 200:
            query = query[:200]

        self.set_status(f"Searching: {query}")
        results = search.find_images(
            query,
            provider=self.config["provider"],
            size=self.config["image_size"],
            safe=self.config["safe_search"],
        )

        try:
            image, used_url = search.fetch_first_usable(results)
        except search.SearchError:
            if original and self.config["restore_clipboard"]:
                try:
                    winclip.set_text(original)
                except RuntimeError:
                    pass
            raise

        image = search.downscale(image, self.config["max_pixels"])
        winclip.set_image(image, used_url if self.config["copy_url_too"] else None)

        self.set_status(f"Copied: {query} ({image.width}x{image.height})")
        self.notify(f"Copied image for {query!r} - press Ctrl+V")

    # ------------------------------------------------------------------ tray

    def notify(self, message: str) -> None:
        if not self.config["notifications"] or self.icon is None:
            return
        try:
            self.icon.notify(message[:250], APP_NAME)
        except Exception:
            pass

    def set_status(self, text: str) -> None:
        self._status = text
        if self.icon is not None:
            self.icon.title = f"{APP_NAME} - {text}"[:127]

    @property
    def status(self) -> str:
        return self._status

    @property
    def armed(self) -> bool:
        """true while a global hotkey is actually bound"""
        return self._hotkey_handle is not None

    def build_tray(self) -> pystray.Icon:
        menu = pystray.Menu(
            pystray.MenuItem("Settings", lambda: self.on_open_settings(), default=True),
            pystray.MenuItem("Search clipboard text now", self._search_clipboard),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: self.on_quit()),
        )
        self.icon = pystray.Icon(APP_NAME, make_tray_image(), APP_NAME, menu)
        self.set_status(self._status)
        return self.icon

    def _search_clipboard(self) -> None:
        """same deal as the hotkey path, just uses whatever text is already on the clipboard"""
        def run():
            with self._busy:
                try:
                    query = winclip.get_text().strip()
                    if not query:
                        raise search.SearchError("Clipboard holds no text.")
                    results = search.find_images(
                        query,
                        provider=self.config["provider"],
                        size=self.config["image_size"],
                        safe=self.config["safe_search"],
                    )
                    image, used_url = search.fetch_first_usable(results)
                    image = search.downscale(image, self.config["max_pixels"])
                    winclip.set_image(
                        image, used_url if self.config["copy_url_too"] else None
                    )
                    self.set_status(f"Copied: {query}")
                    self.notify(f"Copied image for {query!r} - press Ctrl+V")
                except search.SearchError as exc:
                    self.set_status(str(exc))
                    self.notify(str(exc))
                except Exception as exc:
                    traceback.print_exc()
                    self.notify(f"Unexpected error: {exc}")

        if self._busy.locked():
            self.notify("Still working on the previous search.")
            return
        threading.Thread(target=run, daemon=True).start()

    def shutdown(self) -> None:
        self.unregister_hotkey()
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
