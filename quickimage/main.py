"""entry point - wires up config, hotkey, tray icon and the settings window

Tk insists on owning the main thread, so the tray icon runs in a daemon thread and
every tray callback hops back over with root.after()
"""

import sys
import threading
import tkinter as tk
from tkinter import messagebox

import win32api
import win32event
import winerror

from .app import QuickImageApp
from .config import APP_NAME, Config
from .gui import SettingsWindow

MUTEX_NAME = "Global\\QuickImageSingleInstance"


def _claim_single_instance():
    """hand back the mutex handle, or None if another copy already grabbed it"""
    handle = win32event.CreateMutex(None, False, MUTEX_NAME)
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        return None
    return handle


def main() -> int:
    mutex = _claim_single_instance()
    if mutex is None:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            APP_NAME, f"{APP_NAME} is already running - check the system tray."
        )
        return 1

    config = Config()
    app = QuickImageApp(config)

    root = tk.Tk()
    root.withdraw()
    settings = SettingsWindow(root, app)

    def quit_app():
        app.shutdown()
        root.quit()
        root.destroy()

    app.on_open_settings = lambda: root.after(0, settings.show)
    app.on_quit = lambda: root.after(0, quit_app)

    ok, msg = app.register_hotkey()
    app.set_status(msg)
    settings.set_status(msg)

    icon = app.build_tray()
    threading.Thread(target=icon.run, daemon=True).start()

    # a hotkey that wouldnt bind needs the users attention right away
    if not ok or not config["start_minimized"]:
        settings.show()

    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
