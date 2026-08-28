# pyinstaller entry point - it cant point at a package's __main__ directly so this
# tiny shim exists just to give it something to grab onto

from quickimage.main import main

if __name__ == "__main__":
    raise SystemExit(main())
