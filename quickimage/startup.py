"""turn "launch at login" on and off via the windows registry

we use the per-user Run key (HKCU), so this never needs admin rights. the value
we write is whatever command relaunches the app - the frozen .exe if we're built,
otherwise pythonw running the launcher script
"""

import os
import sys

import winreg

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "QuickImage"


def _launch_command() -> str:
    """the command windows should run at login to bring the app back up"""
    if getattr(sys, "frozen", False):
        # packaged as a onefile exe, so just point at ourselves
        return f'"{sys.executable}"'

    # running from source - use pythonw (no console window) on the launcher script
    exe_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(exe_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    launcher = os.path.join(root, "quickimage_launcher.py")
    return f'"{pythonw}" "{launcher}"'


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
        return True
    except OSError:
        return False


def set_enabled(enabled: bool) -> None:
    """add or remove the Run entry, raises OSError if the registry write fails"""
    if enabled:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _launch_command())
    else:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, _VALUE_NAME)
        except FileNotFoundError:
            pass  # already gone, nothing to do
