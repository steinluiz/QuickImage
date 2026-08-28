"""the settings window

the hotkey is the hero here because the hotkey basically is the product - the caps
in the middle show what to press, light up while you rebind, and carry the live
status. everything else writes straight to disk so theres no save button to hunt for
"""

import threading
import tkinter as tk

import keyboard

from . import search, startup, theme as t, widgets as w
from .app import QuickImageApp
from .config import APP_NAME, icon_path

SIZES = ["any", "small", "medium", "large", "huge"]
SIZE_LABELS = {"any": "Any", "small": "Small", "medium": "Medium",
               "large": "Large", "huge": "Huge"}
SAFE_LABELS = {"off": "Off", "medium": "Medium", "high": "Strict"}

PROVIDER_ORDER = ["auto", "duckduckgo", "openverse"]

PAD = 18


class SettingsWindow:
    def __init__(self, root: tk.Tk, app: QuickImageApp):
        self.root = root
        self.app = app
        self.config = app.config
        self.recording = False

        self.win = tk.Toplevel(root, bg=t.INK)
        self.win.title(APP_NAME)
        self.win.resizable(False, False)
        self.win.configure(bg=t.INK)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)
        t.dark_titlebar(self.win)

        # title-bar / taskbar icon, if the ico shipped with the app
        _icon = icon_path()
        if _icon:
            try:
                self.win.iconbitmap(_icon)
            except tk.TclError:
                pass

        self._build()
        self.win.withdraw()

    # ------------------------------------------------------------------ build

    def _build(self) -> None:
        outer = tk.Frame(self.win, bg=t.INK, padx=PAD, pady=16)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        self._build_header(outer)
        self._build_hero(outer)
        self._build_source(outer)
        self._build_images(outer)
        self._build_behaviour(outer)
        self._build_footer(outer)

    def _build_header(self, parent) -> None:
        row = tk.Frame(parent, bg=t.INK)
        row.grid(row=0, column=0, sticky="ew")
        self.dot = w.StatusDot(row)
        self.dot.pack(side="left", pady=(0, 2))
        w.label(row, APP_NAME, bg=t.INK, font=t.display(12, "bold")).pack(
            side="left", padx=(8, 0)
        )
        w.label(row, "select → press → paste", bg=t.INK, fg=t.FAINT,
                font=t.body(9)).pack(side="right")

    def _build_hero(self, parent) -> None:
        hero = tk.Frame(parent, bg=t.INK)
        hero.grid(row=1, column=0, sticky="ew", pady=(14, 16))
        hero.columnconfigure(0, weight=1)

        self.keycaps = w.KeycapRow(hero, self.config["hotkey"])
        self.keycaps.grid(row=0, column=0, sticky="ew")

        self.hint = w.label(hero, "", bg=t.INK, fg=t.MUTED, font=t.body(9),
                            anchor="center", justify="center", wraplength=420)
        self.hint.grid(row=1, column=0, sticky="ew", pady=(2, 12))

        self.rebind_btn = w.Button(hero, "Rebind", command=self.record_hotkey)
        self.rebind_btn.grid(row=2, column=0)

    def _build_source(self, parent) -> None:
        box = w.card(parent)
        box.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        box.columnconfigure(0, weight=1)
        inner = tk.Frame(box, bg=t.SURFACE, padx=14, pady=12)
        inner.grid(sticky="ew")
        inner.columnconfigure(0, weight=1)

        w.eyebrow(inner, "Source").grid(row=0, column=0, sticky="w")
        self.provider = w.Segmented(
            inner,
            [search.PROVIDER_LABELS[name] for name in PROVIDER_ORDER],
            search.PROVIDER_LABELS.get(self.config["provider"], "Auto"),
            command=self._on_provider,
        )
        self.provider.configure(bg=t.SURFACE)
        self.provider.grid(row=1, column=0, sticky="ew", pady=(8, 6))

        self.provider_hint = w.label(
            inner, search.PROVIDER_HINTS.get(self.config["provider"], ""),
            fg=t.MUTED, font=t.body(9), wraplength=400,
        )
        self.provider_hint.grid(row=2, column=0, sticky="w")

    def _build_images(self, parent) -> None:
        box = w.card(parent)
        box.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        box.columnconfigure(0, weight=1)
        inner = tk.Frame(box, bg=t.SURFACE, padx=14, pady=12)
        inner.grid(sticky="ew")
        inner.columnconfigure(1, weight=1)

        w.eyebrow(inner, "Images").grid(row=0, column=0, columnspan=2, sticky="w")

        w.label(inner, "Preferred size", fg=t.MUTED).grid(
            row=1, column=0, sticky="w", pady=(10, 0)
        )
        stored_size = self.config["image_size"]
        self.size = w.Dropdown(
            inner, [SIZE_LABELS[s] for s in SIZES],
            SIZE_LABELS.get(stored_size, "Large"), command=self._on_size, width=8,
        )
        self.size.grid(row=1, column=1, sticky="e", pady=(10, 0))

        w.label(inner, "SafeSearch", fg=t.MUTED).grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        self.safe = w.Segmented(
            inner, list(SAFE_LABELS.values()),
            SAFE_LABELS.get(self.config["safe_search"], "Off"),
            command=self._on_safe,
        )
        self.safe.configure(bg=t.SURFACE, width=180)
        self.safe.grid(row=2, column=1, sticky="e", pady=(10, 0))

        edge_row = tk.Frame(inner, bg=t.SURFACE)
        edge_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        edge_row.columnconfigure(0, weight=1)
        w.label(edge_row, "Maximum edge", fg=t.MUTED).grid(row=0, column=0, sticky="w")
        self.edge_value = w.label(edge_row, "", fg=t.AMBER, font=t.mono(9))
        self.edge_value.grid(row=0, column=1, sticky="e")
        self.edge = w.Slider(
            edge_row, 0, 4000, self.config["max_pixels"], step=100,
            command=self._on_edge,
        )
        self.edge.configure(bg=t.SURFACE)
        self.edge.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self._render_edge_value()

    def _build_behaviour(self, parent) -> None:
        box = w.card(parent)
        box.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        box.columnconfigure(0, weight=1)
        inner = tk.Frame(box, bg=t.SURFACE, padx=14, pady=12)
        inner.grid(sticky="ew")
        inner.columnconfigure(0, weight=1)

        w.eyebrow(inner, "Behaviour").grid(row=0, column=0, columnspan=2, sticky="w")

        self.toggles = {}
        rows = [
            ("copy_url_too", "Copy the image URL as text too"),
            ("restore_clipboard", "Restore the clipboard when a search fails"),
            ("notifications", "Show notifications"),
            ("start_minimized", "Start hidden in the tray"),
        ]
        for index, (key, text) in enumerate(rows, start=1):
            w.label(inner, text).grid(row=index, column=0, sticky="w", pady=6)
            toggle = w.Toggle(
                inner, self.config[key],
                command=lambda value, k=key: self._on_toggle(k, value),
            )
            toggle.configure(bg=t.SURFACE)
            toggle.grid(row=index, column=1, sticky="e", padx=(12, 0))
            self.toggles[key] = toggle

        # this one is a windows setting (a registry Run entry), not saved config
        launch_row = len(rows) + 1
        w.label(inner, "Start with Windows").grid(
            row=launch_row, column=0, sticky="w", pady=6
        )
        self.startup_toggle = w.Toggle(
            inner, startup.is_enabled(), command=self._on_startup
        )
        self.startup_toggle.configure(bg=t.SURFACE)
        self.startup_toggle.grid(row=launch_row, column=1, sticky="e", padx=(12, 0))

    def _build_footer(self, parent) -> None:
        row = tk.Frame(parent, bg=t.INK)
        row.grid(row=5, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)
        w.label(row, "Changes save as you make them.", bg=t.INK, fg=t.FAINT,
                font=t.body(8)).grid(row=0, column=0, sticky="w")
        self.test_btn = w.Button(row, "Test search", command=self.test_search)
        self.test_btn.grid(row=0, column=1, sticky="e")

    # ---------------------------------------------------------------- changes

    def _persist(self, key: str, value) -> None:
        self.config[key] = value
        self.config.save()

    def _on_provider(self, label: str) -> None:
        name = next(k for k in PROVIDER_ORDER if search.PROVIDER_LABELS[k] == label)
        self._persist("provider", name)
        self.provider_hint.config(text=search.PROVIDER_HINTS[name])

    def _on_size(self, label: str) -> None:
        name = next(k for k, v in SIZE_LABELS.items() if v == label)
        self._persist("image_size", name)

    def _on_safe(self, label: str) -> None:
        name = next(k for k, v in SAFE_LABELS.items() if v == label)
        self._persist("safe_search", name)

    def _render_edge_value(self) -> None:
        pixels = self.edge.get()
        self.edge_value.config(text="Original" if pixels == 0 else f"{pixels} px")

    def _on_edge(self, pixels: int) -> None:
        self._render_edge_value()
        self._persist("max_pixels", pixels)

    def _on_toggle(self, key: str, value: bool) -> None:
        self._persist(key, value)

    def _on_startup(self, value: bool) -> None:
        try:
            startup.set_enabled(value)
        except OSError as exc:
            # registry write got refused, flip the switch back so it stays honest
            self.startup_toggle.value = not value
            self.startup_toggle._draw()
            self.set_status(f"Couldn't change startup: {exc}", ok=False)

    # ----------------------------------------------------------------- hotkey

    def record_hotkey(self) -> None:
        """grab the next combo the user presses

        we unbind the live hotkey first, otherwise recording it would just fire
        off a search instead of getting captured
        """
        if self.recording:
            return
        self.recording = True
        self.rebind_btn.set_text("Listening")
        self.rebind_btn.set_enabled(False)
        self.keycaps.set_recording(True)
        self.set_status("Press the combination you want.")
        self.app.unregister_hotkey()

        def worker():
            combo, error = None, None
            try:
                combo = keyboard.read_hotkey(suppress=False)
            except Exception as exc:
                error = str(exc)
            self.root.after(0, lambda: self._finish_record(combo, error))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_record(self, combo: str | None, error: str | None) -> None:
        self.recording = False
        self.keycaps.set_recording(False)
        self.rebind_btn.set_text("Rebind")
        self.rebind_btn.set_enabled(True)

        if combo:
            self._persist("hotkey", combo)
            self.keycaps.set_hotkey(combo)

        ok, message = self.app.register_hotkey()
        self.app.set_status(message)
        self.set_status(f"Recording failed: {error}" if error else message,
                        ok=ok if not error else False)

    # ------------------------------------------------------------------- test

    def test_search(self) -> None:
        self.test_btn.set_text("Searching")
        self.test_btn.set_enabled(False)
        self.set_status("Running a test search...")

        def worker():
            try:
                results = search.find_images(
                    "golden retriever",
                    provider=self.config["provider"],
                    size=self.config["image_size"],
                    safe=self.config["safe_search"],
                    count=5,
                )
                image, _url = search.fetch_first_usable(results)
                message = f"Works. Got a {image.width}x{image.height} image."
                ok = True
            except Exception as exc:
                message, ok = str(exc), False
            self.root.after(0, lambda: self._finish_test(message, ok))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_test(self, message: str, ok: bool) -> None:
        self.test_btn.set_text("Test search")
        self.test_btn.set_enabled(True)
        self.set_status(message, ok=ok)

    # ----------------------------------------------------------------- status

    def set_status(self, text: str, ok: bool | None = None) -> None:
        self.hint.config(text=text)
        if self.recording:
            self.dot.set_color(t.AMBER)
        elif ok is False:
            self.dot.set_color(t.RED)
        elif ok is True:
            self.dot.set_color(t.GREEN)
        else:
            self.dot.set_color(t.AMBER if self.app.armed else t.FAINT)

    # -------------------------------------------------------------- lifecycle

    def show(self) -> None:
        self.set_status(self.app.status)
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

    def hide(self) -> None:
        self.win.withdraw()
