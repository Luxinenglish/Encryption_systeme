import os
import tkinter as tk
from tkinter import filedialog, messagebox

from constants import (
    ACCENT, BG, BG2, BG3, BORDER, MUTED, SUCCESS, TEXT,
    F_BODY, F_SMALL,
)
from translator import t

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    ROOT_CLASS = TkinterDnD.Tk
    DND_AVAILABLE = True
except ImportError:
    ROOT_CLASS = tk.Tk
    DND_AVAILABLE = False


class DropZone(tk.Frame):
    def __init__(self, parent, height: int = 150, **kwargs):
        super().__init__(parent, bg=BG2, height=height, **kwargs)
        self.pack_propagate(False)
        self.selected_path: str | None = None
        self.is_file: bool = False
        self._callback = None
        self._placeholder = t(
            "dropzone.placeholder",
            "📂📄  Drag a folder or file here\n\nor click to browse a file",
        )

        self._border = tk.Frame(self, bg=BORDER, padx=2, pady=2)
        self._border.pack(fill="both", expand=True)

        self._inner = tk.Frame(self._border, bg=BG2)
        self._inner.pack(fill="both", expand=True)

        self._lbl = tk.Label(
            self._inner,
            text=self._placeholder,
            font=F_BODY,
            fg=MUTED,
            bg=BG2,
            justify="center",
            cursor="hand2",
        )
        self._lbl.pack(fill="both", expand=True)

        for w in (self._lbl, self._inner):
            w.bind("<Button-1>", self._browse)
            w.bind("<Enter>", lambda _e: self._set_border(ACCENT))
            w.bind("<Leave>", lambda _e: self._set_border(BORDER if not self.selected_path else SUCCESS))
            if DND_AVAILABLE:
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_dnd)

    def on_select(self, cb):
        self._callback = cb

    def _set_border(self, color: str):
        self._border.config(bg=color)

    def _on_dnd(self, event):
        raw = event.data.strip()
        if raw.startswith("{"):
            path = raw[1: raw.index("}")]
        else:
            path = raw.split()[0]
        self._set_path(path)

    def _browse(self, _event=None):
        path = filedialog.askopenfilename(title=t("dropzone.select_file", "Select a file"))
        if path:
            self._set_path(path)

    def browse_folder(self):
        path = filedialog.askdirectory(title=t("dropzone.select_folder", "Select a folder"))
        if path:
            self._set_path(path)

    def _set_path(self, path: str):
        if os.path.isfile(path):
            self.selected_path = path
            self.is_file = True
            self._lbl.config(
                text=t("dropzone.selected_file", "✅  📄 {name}", name=os.path.basename(path)),
                fg=SUCCESS,
                font=("Segoe UI", 12, "bold"),
            )
            self._set_border(SUCCESS)
            if self._callback:
                self._callback(path)
        elif os.path.isdir(path):
            self.selected_path = path
            self.is_file = False
            self._lbl.config(
                text=t("dropzone.selected_folder", "✅  📂 {name}", name=os.path.basename(path)),
                fg=SUCCESS,
                font=("Segoe UI", 12, "bold"),
            )
            self._set_border(SUCCESS)
            if self._callback:
                self._callback(path)
        else:
            messagebox.showerror(
                t("errors.error", "Error"),
                t("errors.drag_invalid", "Please drop a valid file or folder."),
            )

    def reset(self):
        self.selected_path = None
        self.is_file = False
        self._lbl.config(text=self._placeholder, fg=MUTED, font=F_BODY)
        self._set_border(BORDER)


def action_btn(parent, text: str, command) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        font=("Segoe UI", 12, "bold"),
        fg=TEXT,
        bg=ACCENT,
        activeforeground=TEXT,
        activebackground="#c0392b",
        relief="flat",
        bd=0,
        pady=12,
        cursor="hand2",
        command=command,
    )


def ghost_btn(parent, text: str, command) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        font=F_SMALL,
        fg=MUTED,
        bg=BG,
        activeforeground=TEXT,
        activebackground=BG2,
        relief="flat",
        bd=0,
        cursor="hand2",
        command=command,
    )
