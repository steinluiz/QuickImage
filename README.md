
<p align="center">
  <img src="https://github.com/user-attachments/assets/953f61d8-01bb-486e-995b-89a40bd5ab70" width="96">
</p>

<h1 align="center">QuickImage</h1>

<p align="center">Select any text, press one key, and the first image is on your clipboard.</p>


## How to use it

1. **Highlight** some text — a word in a message, a name on a website, anything you can select.
2. Press **`Alt + I`**.
3. Press **`Ctrl + V`** where you want the image (Word, Paint, WhatsApp, Discord, PowerPoint, an email…).

That's it. The image is already on your clipboard.

> Example: a friend types *"golden retriever"*, you select it, press `Alt + I`, then paste a photo of a golden retriever straight into the chat.

---

## Download & run (easiest)

1. Download **`QuickImage.exe`**.
2. Double-click it.
3. A small icon appears near your clock (bottom-right of the screen). That means it's running.

You're done. Try it anywhere: select text → `Alt + I` → `Ctrl + V`.

---

## The settings window

Right-click the tray icon (near the clock) and choose **Settings**, or double-click the icon.

| Setting | What it does |
| --- | --- |
| **The keys in the middle** | Your shortcut. Click **Rebind** to pick a different one if `Alt + I` clashes with something. |
| **Source** | Where images come from. Leave it on **Auto** — it just works, no account needed. |
| **Preferred size** | Bigger or smaller images. **Large** is a good default. |
| **SafeSearch** | Filter out adult content. |
| **Maximum edge** | Shrinks huge images so they paste faster. |
| **Copy the image URL too** | Also copies the image's web link as text. |
| **Show notifications** | A little popup when an image is copied. |
| **Start hidden in the tray** | Skip the settings window when it launches. |
| **Start with Windows** | Will start when you turn on your computer. |

Everything you change is saved instantly.

---

## If something doesn't work

**"No text selected"**
You have to *highlight* the text first, then press `Alt + I`. Also make sure the text is selectable (a few apps block copying).

**Nothing happens / no image**
- Check you're connected to the internet.
- Open Settings and click **Test search** — it tells you if the image source is reachable.

**The shortcut does nothing in some apps**
A few programs run "as administrator". To use the shortcut inside those, right-click `QuickImage.exe` → **Run as administrator**.

**I want to close it**
Right-click the tray icon → **Quit**.

---

## For developers

Prefer to run from the source code? Install the dependencies once, then launch it:

```bat
py -m pip install -r requirements.txt
pythonw -m quickimage
```

(`pythonw` runs it with no console window. Use `py -m quickimage` instead if you want to see logs and errors.)

Build your own single-file `.exe`:

```bat
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --onefile --windowed --name QuickImage --icon Icon.ico --add-data "Icon.ico;." --hidden-import win32timezone quickimage_launcher.py
```

The result lands in `dist\QuickImage.exe`.

**How images are found:** two keyless sources, no account or API key. **DuckDuckGo** for whole-web results, with **Openverse** (openly licensed images) as an automatic fallback.

Settings are stored in `%APPDATA%\QuickImage\config.json`.

**Note:** Windows only.

## License

MIT — free to use, copy, and modify. See [LICENSE](LICENSE).
