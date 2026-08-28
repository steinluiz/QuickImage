# QuickImage

**Select any text, press one key, and the first image from the web is copied — ready to paste anywhere.**

No tabs to open, no searching, no saving files. Highlight a word, hit `Alt + I`, then `Ctrl + V` wherever you want the picture.

---

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

**No installation. No Python. No extra folder.** It's one single file — you can even keep it on your Desktop.

### "Windows protected your PC" popup?

That's normal for small free apps that aren't signed. Click **More info** → **Run anyway**. It's safe.

### Want it to start with Windows?

Press `Win + R`, type `shell:startup`, press Enter, and drop a shortcut to `QuickImage.exe` in the folder that opens.

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

Everything you change is saved instantly — there's no Save button.

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

**How images are found:** two keyless sources, no account or API key. **DuckDuckGo** for whole-web results, with **Openverse** (openly licensed images) as an automatic fallback. Google was dropped — it closed whole-web search to new users in January 2026.

**Project layout:**

```
quickimage/
  main.py       starts everything up
  app.py        the hotkey, the worker, the tray icon
  gui.py        the settings window
  widgets.py    the custom-drawn controls
  theme.py      colors and fonts
  search.py     finds and downloads the image
  selection.py  reads the highlighted text
  winclip.py    puts the image on the clipboard
  config.py     saves your settings
```

Settings are stored in `%APPDATA%\QuickImage\config.json`.

**Note:** Windows only.

## License

MIT — free to use, copy, and modify. See [LICENSE](LICENSE).
