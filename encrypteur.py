#!/usr/bin/env python3
"""
Folder Encryption System
Drag a folder to encrypt or decrypt it with a unique key.
Algorithm: Fernet (AES-128-CBC + HMAC-SHA256)
"""

import ctypes
import sys

from app import App

if __name__ == "__main__":
    # Tell Windows to use the app's own icon in the taskbar
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("lux.encryption_system")

    app = App()
    app.mainloop()
