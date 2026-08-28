"""hand-drawn widgets. tk's stock controls just cant be themed far enough, so the
handful of interactive bits this app needs get drawn on canvases instead
"""

import tkinter as tk

from . import theme as t

# nicer looking names for the raw tokens the keyboard lib hands back
KEY_LABELS = {
    "ctrl": "Ctrl", "left ctrl": "Ctrl", "right ctrl": "Ctrl",
    "alt": "Alt", "left alt": "Alt", "right alt": "Alt", "alt gr": "AltGr",
    "shift": "Shift", "left shift": "Shift", "right shift": "Shift",
    "windows": "Win", "left windows": "Win", "right windows": "Win",
    "space": "Space", "enter": "Enter", "esc": "Esc", "tab": "Tab",
    "backspace": "Bksp", "delete": "Del", "insert": "Ins",
    "page up": "PgUp", "page down": "PgDn", "caps lock": "Caps",
    "up": "Up", "down": "Down", "left": "Left", "right": "Right",
}


def key_labels(hotkey: str) -> list[str]:
    parts = [p.strip() for p in hotkey.split("+") if p.strip()]
    return [KEY_LABELS.get(p.lower(), p.upper() if len(p) == 1 else p.title())
            for p in parts]


class KeycapRow(tk.Canvas):
    """the hero bit - the hotkey drawn as actual physical keycaps

    doubles as the recorder too, so the caps themselves light up while were
    sitting there waiting for a new combo
    """

    HEIGHT = 62

    def __init__(self, parent, hotkey: str, **kwargs):
        super().__init__(parent, height=self.HEIGHT, bg=t.INK,
                         highlightthickness=0, bd=0, **kwargs)
        self._keys = key_labels(hotkey)
        self._recording = False
        self._phase = 0.0
        self._pulse_job = None
        self.bind("<Configure>", lambda _e: self._draw())

    def set_hotkey(self, hotkey: str) -> None:
        self._keys = key_labels(hotkey)
        self._draw()

    def set_recording(self, recording: bool) -> None:
        self._recording = recording
        if recording and self._pulse_job is None:
            self._pulse()
        elif not recording and self._pulse_job is not None:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None
            self._draw()

    def _pulse(self) -> None:
        self._phase = (self._phase + 0.06) % 1.0
        self._draw()
        self._pulse_job = self.after(40, self._pulse)

    def _draw(self) -> None:
        self.delete("all")
        width = self.winfo_width()
        if width <= 1:
            return

        cap_font = t.mono(13, "bold")
        gap, pad, cap_h = 12, 26, 44
        probe = tk.font.Font(font=cap_font)
        widths = [max(46, probe.measure(k) + pad) for k in self._keys]
        total = sum(widths) + gap * 2 * (len(self._keys) - 1)

        if self._recording:
            # slow triangle wave so the caps kinda breathe instead of blinking
            swing = abs(self._phase * 2 - 1)
            face = t.blend(t.AMBER_SOFT, t.SURFACE, swing)
            edge = t.blend(t.AMBER, t.AMBER_DEEP, swing)
            ink = t.AMBER
        else:
            face, edge, ink = t.SURFACE_HI, t.EDGE_HI, t.TEXT

        x = (width - total) / 2
        y = (self.HEIGHT - cap_h) / 2
        for index, (label, cap_w) in enumerate(zip(self._keys, widths)):
            if index:
                self.create_text(x - gap, y + cap_h / 2, text="+",
                                 fill=t.FAINT, font=t.body(11))
            t.round_rect(self, x, y + 3, x + cap_w, y + cap_h + 3, 9,
                         fill=t.INK, outline="")           # little drop shadow
            t.round_rect(self, x, y, x + cap_w, y + cap_h, 9,
                         fill=face, outline=edge, width=1)
            self.create_line(x + 9, y + 1, x + cap_w - 9, y + 1,
                             fill=t.blend(face, t.TEXT, 0.10))  # bevel across the top
            self.create_text(x + cap_w / 2, y + cap_h / 2, text=label,
                             fill=ink, font=cap_font)
            x += cap_w + gap * 2


class StatusDot(tk.Canvas):
    """six pixels of state - amber armed, red failed, grey idle"""

    def __init__(self, parent):
        super().__init__(parent, width=10, height=10, bg=t.INK,
                         highlightthickness=0, bd=0)
        self._item = self.create_oval(2, 2, 9, 9, fill=t.FAINT, outline="")

    def set_color(self, color: str) -> None:
        self.itemconfig(self._item, fill=color)


class Segmented(tk.Canvas):
    """row of pick-one options, stretches to fill whatever parent its in"""

    HEIGHT = 34

    def __init__(self, parent, options: list[str], value: str, command=None):
        super().__init__(parent, height=self.HEIGHT, bg=t.INK,
                         highlightthickness=0, bd=0)
        self.options = options
        self.value = value if value in options else options[0]
        self.command = command
        self._hover = None
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda _e: self._set_hover(None))

    def _index_at(self, x: int) -> int:
        width = max(self.winfo_width(), 1)
        return min(int(x / (width / len(self.options))), len(self.options) - 1)

    def _on_click(self, event) -> None:
        chosen = self.options[self._index_at(event.x)]
        if chosen != self.value:
            self.value = chosen
            self._draw()
            if self.command:
                self.command(chosen)

    def _on_motion(self, event) -> None:
        self._set_hover(self._index_at(event.x))

    def _set_hover(self, index) -> None:
        if index != self._hover:
            self._hover = index
            self._draw()

    def _draw(self) -> None:
        self.delete("all")
        width = self.winfo_width()
        if width <= 1:
            return
        t.round_rect(self, 0, 0, width, self.HEIGHT, 9,
                     fill=t.SURFACE, outline=t.EDGE, width=1)
        slot = width / len(self.options)
        for index, option in enumerate(self.options):
            x0, x1 = index * slot, (index + 1) * slot
            selected = option == self.value
            if selected:
                t.round_rect(self, x0 + 3, 3, x1 - 3, self.HEIGHT - 3, 7,
                             fill=t.AMBER, outline="")
                fill, font = t.INK, t.body(9, "bold")
            elif index == self._hover:
                t.round_rect(self, x0 + 3, 3, x1 - 3, self.HEIGHT - 3, 7,
                             fill=t.SURFACE_HI, outline="")
                fill, font = t.TEXT, t.body(9)
            else:
                fill, font = t.MUTED, t.body(9)
            self.create_text((x0 + x1) / 2, self.HEIGHT / 2, text=option,
                             fill=fill, font=font)


class Toggle(tk.Canvas):
    """pill switch that slides a little so you can actually see the state change"""

    W, H = 42, 23

    def __init__(self, parent, value: bool, command=None):
        super().__init__(parent, width=self.W, height=self.H, bg=t.INK,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.value = bool(value)
        self.command = command
        self._pos = 1.0 if self.value else 0.0
        self._job = None
        self.bind("<Button-1>", lambda _e: self.toggle())
        self._draw()

    def toggle(self) -> None:
        self.value = not self.value
        self._animate()
        if self.command:
            self.command(self.value)

    def _animate(self) -> None:
        target = 1.0 if self.value else 0.0
        if self._job is not None:
            self.after_cancel(self._job)
        step = 0.16 if target > self._pos else -0.16

        def frame():
            self._pos = min(1.0, max(0.0, self._pos + step))
            self._draw()
            if (step > 0 and self._pos < 1.0) or (step < 0 and self._pos > 0.0):
                self._job = self.after(12, frame)
            else:
                self._job = None

        frame()

    def _draw(self) -> None:
        self.delete("all")
        track = t.blend(t.SURFACE_HI, t.AMBER, self._pos)
        border = t.blend(t.EDGE_HI, t.AMBER, self._pos)
        t.round_rect(self, 1, 1, self.W - 1, self.H - 1, (self.H - 2) / 2,
                     fill=track, outline=border, width=1)
        radius = (self.H - 8) / 2
        cx = 5 + radius + self._pos * (self.W - 10 - radius * 2)
        cy = self.H / 2
        self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                         fill=t.blend(t.MUTED, t.INK, self._pos), outline="")


class Slider(tk.Canvas):
    """numeric slider with a live label, snaps to a step so the value stays tidy"""

    HEIGHT = 30

    def __init__(self, parent, minimum: int, maximum: int, value: int,
                 step: int = 100, command=None):
        super().__init__(parent, height=self.HEIGHT, bg=t.INK,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.minimum, self.maximum, self.step = minimum, maximum, step
        self.value = self._clamp(value)
        self.command = command
        self._dragging = False
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _clamp(self, value: int) -> int:
        value = max(self.minimum, min(self.maximum, int(value)))
        return round(value / self.step) * self.step

    def get(self) -> int:
        return self.value

    def _track(self):
        return 10, max(self.winfo_width() - 10, 20)

    def _on_press(self, event) -> None:
        self._dragging = True
        self._on_drag(event)

    def _on_drag(self, event) -> None:
        if not self._dragging:
            return
        x0, x1 = self._track()
        ratio = (event.x - x0) / max(x1 - x0, 1)
        self.value = self._clamp(self.minimum + ratio * (self.maximum - self.minimum))
        self._draw()

    def _on_release(self, _event) -> None:
        self._dragging = False
        if self.command:
            self.command(self.value)

    def _draw(self) -> None:
        self.delete("all")
        width = self.winfo_width()
        if width <= 1:
            return
        x0, x1 = self._track()
        y = self.HEIGHT / 2
        ratio = (self.value - self.minimum) / max(self.maximum - self.minimum, 1)
        knob_x = x0 + ratio * (x1 - x0)

        self.create_line(x0, y, x1, y, fill=t.EDGE, width=4, capstyle="round")
        if knob_x > x0 + 1:
            self.create_line(x0, y, knob_x, y, fill=t.AMBER, width=4,
                             capstyle="round")
        self.create_oval(knob_x - 7, y - 7, knob_x + 7, y + 7,
                         fill=t.TEXT, outline=t.INK, width=2)


class Dropdown(tk.Menubutton):
    """tk's menubutton is one of like two stock widgets that actually themes cleanly"""

    def __init__(self, parent, options: list[str], value: str, command=None,
                 width: int = 10):
        self.var = tk.StringVar(value=value)
        super().__init__(
            parent, textvariable=self.var, width=width, anchor="w",
            bg=t.SURFACE, fg=t.TEXT, activebackground=t.SURFACE_HI,
            activeforeground=t.TEXT, relief="flat", bd=0, padx=10, pady=6,
            font=t.body(9), highlightthickness=1, highlightbackground=t.EDGE,
            highlightcolor=t.EDGE, cursor="hand2", indicatoron=False,
        )
        self.command = command
        menu = tk.Menu(
            self, tearoff=0, bg=t.SURFACE, fg=t.TEXT, activebackground=t.AMBER,
            activeforeground=t.INK, bd=0, relief="flat", font=t.body(9),
            activeborderwidth=0,
        )
        for option in options:
            menu.add_command(label=option, command=lambda o=option: self._choose(o))
        self.configure(menu=menu)
        self.bind("<Enter>", lambda _e: self.configure(bg=t.SURFACE_HI))
        self.bind("<Leave>", lambda _e: self.configure(bg=t.SURFACE))

    def _choose(self, option: str) -> None:
        self.var.set(option)
        if self.command:
            self.command(option)


class Button(tk.Canvas):
    """flat ghost button, hover lifts it a shade and the text stays put"""

    HEIGHT = 34

    def __init__(self, parent, text: str, command=None, width: int | None = None):
        self._text = text
        probe = tk.font.Font(font=t.body(9, "bold"))
        width = width or probe.measure(text) + 34
        super().__init__(parent, width=width, height=self.HEIGHT, bg=t.INK,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.command = command
        self._hover = False
        self._enabled = True
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self._draw()

    def set_text(self, text: str) -> None:
        self._text = text
        self._draw()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def _set_hover(self, hover: bool) -> None:
        self._hover = hover
        self._draw()

    def _on_click(self, _event) -> None:
        if self._enabled and self.command:
            self.command()

    def _draw(self) -> None:
        self.delete("all")
        width = int(self["width"])
        fill = t.SURFACE_HI if self._hover else t.SURFACE
        outline, ink = t.EDGE_HI if self._hover else t.EDGE, t.TEXT
        if not self._enabled:
            fill, ink, outline = t.SURFACE, t.FAINT, t.EDGE
        t.round_rect(self, 1, 1, width - 1, self.HEIGHT - 1, 8,
                     fill=fill, outline=outline, width=1)
        self.create_text(width / 2, self.HEIGHT / 2, text=self._text,
                         fill=ink, font=t.body(9, "bold"))


def card(parent) -> tk.Frame:
    frame = tk.Frame(parent, bg=t.SURFACE, highlightbackground=t.EDGE,
                     highlightthickness=1, bd=0)
    return frame


def eyebrow(parent, text: str, bg: str = t.SURFACE) -> tk.Label:
    return tk.Label(parent, text=text.upper(), bg=bg, fg=t.FAINT,
                    font=t.body(8, "bold"))


def label(parent, text: str, bg: str = t.SURFACE, fg: str = t.TEXT,
          font=None, **kwargs) -> tk.Label:
    kwargs.setdefault("justify", "left")
    kwargs.setdefault("anchor", "w")
    return tk.Label(parent, text=text, bg=bg, fg=fg, font=font or t.body(9),
                    **kwargs)
