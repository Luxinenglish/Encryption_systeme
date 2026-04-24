import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


from constants import (
    ACCENT, BG, BG2, BG3, ERROR, MUTED, SUCCESS, TEXT,
    F_BODY, F_MONO, F_SMALL, F_TITLE, APP_VERSION, GITHUB_REPO,
)
from crypto import (
    ALGO_FERNET, ALGO_LABELS,
    decrypt_file, decrypt_folder,
    encrypt_file, encrypt_folder,
)
from key_manager import KeyManager
from auth_manager import AuthManager
from updater import UpdateService
from widgets import DND_AVAILABLE, ROOT_CLASS, DropZone, action_btn, ghost_btn


class App(ROOT_CLASS):
    def __init__(self):
        super().__init__()
        self.title("Encryption System")
        self.geometry("700x620")
        self.minsize(600, 520)
        self.configure(bg=BG)
        self._set_icon()
        self._auth = AuthManager()
        self._updater = UpdateService(repo=GITHUB_REPO, current_version=APP_VERSION)
        self._is_checking_update = False
        vault_key = self._require_access_password()
        if not vault_key:
            self.destroy()
            return
        self._km = KeyManager(vault_key=vault_key)
        self._build_ui()
        self.bind("<Configure>", self._on_resize)
        self.after(1500, self._check_updates_silent)



    # ── Icon ──────────────────────────────────────────────────────────────────

    def _set_icon(self):
        icon_path = Path(__file__).parent / "img" / "logo.png"
        if icon_path.exists():
            icon = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, icon)
            self._icon = icon  # keep a reference to prevent garbage collection

    # ── Access password ───────────────────────────────────────────────────────

    def _require_access_password(self) -> str | None:
        if not self._auth.is_configured():
            messagebox.showinfo(
                "Premiere utilisation",
                "Definis un mot de passe pour proteger l'acces au coffre."
            )
            return self._show_setup_password_dialog()
        return self._show_unlock_dialog( )

    def _show_setup_password_dialog(self) -> str | None:
        popup = tk.Toplevel(self, bg=BG)
        popup.title("Configurer le mot de passe")
        popup.geometry("420x250")
        popup.resizable(False, False)
        popup.grab_set()

        result: dict[str, str | None] = {"vault_key": None}

        tk.Label(
            popup,
            text="Nouveau mot de passe",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=BG,
        ).pack(anchor="w", padx=20, pady=(20, 6))

        pwd_var = tk.StringVar()
        pwd2_var = tk.StringVar()

        tk.Entry(
            popup,
            textvariable=pwd_var,
            show="*",
            font=F_BODY,
            fg=TEXT,
            bg=BG3,
            insertbackground=TEXT,
            relief="flat",
        ).pack(fill="x", padx=20, ipady=8)

        tk.Label(
            popup,
            text="Confirmer le mot de passe",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=BG,
        ).pack(anchor="w", padx=20, pady=(14, 6))

        tk.Entry(
            popup,
            textvariable=pwd2_var,
            show="*",
            font=F_BODY,
            fg=TEXT,
            bg=BG3,
            insertbackground=TEXT,
            relief="flat",
        ).pack(fill="x", padx=20, ipady=8)

        status = tk.Label(popup, text="", font=F_SMALL, fg=ERROR, bg=BG)
        status.pack(anchor="w", padx=20, pady=(8, 0))

        def _save():
            pwd = pwd_var.get()
            pwd2 = pwd2_var.get()

            if len(pwd) < 8:
                status.config(text="Le mot de passe doit faire au moins 8 caracteres.")
                return
            if pwd != pwd2:
                status.config(text="Les mots de passe ne correspondent pas.")
                return

            self._auth.setup_password(pwd)
            result["vault_key"] = self._auth.get_vault_key(pwd)
            popup.destroy()

        def _cancel():
            popup.destroy()
        tk.Button(
            popup,
            text="Enregistrer",
            font=F_BODY,
            fg=TEXT,
            bg=SUCCESS,
            activeforeground=TEXT,
            activebackground="#00a381",
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=_save,
        ).pack(fill="x", padx=20, pady=(14, 6))

        tk.Button(
            popup,
            text="Quitter",
            font=F_BODY,
            fg=MUTED,
            bg=BG2,
            activeforeground=TEXT,
            activebackground=BG3,
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=_cancel,
        ).pack(fill="x", padx=20)

        popup.protocol("WM_DELETE_WINDOW", _cancel)
        popup.wait_window()
        return result["vault_key"]

    def _show_unlock_dialog(self) -> str | None:
        popup = tk.Toplevel(self, bg=BG)
        popup.title("Deverrouiller le coffre")
        popup.geometry("420x180")
        popup.resizable(False, False)
        popup.grab_set()

        result: dict[str, str | None] = {"vault_key": None}

        tk.Label(
            popup,
            text="Mot de passe",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=BG,
        ).pack(anchor="w", padx=20, pady=(20, 6))

        pwd_var = tk.StringVar()
        entry = tk.Entry(
            popup,
            textvariable=pwd_var,
            show="*",
            font=F_BODY,
            fg=TEXT,
            bg=BG3,
            insertbackground=TEXT,
            relief="flat",
        )
        entry.pack(fill="x", padx=20, ipady=8)
        entry.focus_set()

        status = tk.Label(popup, text="", font=F_SMALL, fg=ERROR, bg=BG)
        status.pack(anchor="w", padx=20, pady=(8, 0))

        def _unlock():
            pwd = pwd_var.get()
            if self._auth.verify_password(pwd):
                result["vault_key"] = self._auth.get_vault_key(pwd)
                popup.destroy()
            else:
                status.config(text="Mot de passe incorrect.")

        def _cancel():
            popup.destroy()
        tk.Button(
            popup,
            text="Ouvrir",
            font=F_BODY,
            fg=TEXT,
            bg=ACCENT,
            activeforeground=TEXT,
            activebackground="#c0392b",
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=_unlock,
        ).pack(fill="x", padx=20, pady=(12, 6))

        tk.Button(
            popup,
            text="Quitter",
            font=F_BODY,
            fg=MUTED,
            bg=BG2,
            activeforeground=TEXT,
            activebackground=BG3,
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=_cancel,
        ).pack(fill="x", padx=20)

        entry.bind("<Return>", lambda _e: _unlock())
        popup.protocol("WM_DELETE_WINDOW", _cancel)
        popup.wait_window()
        return result["vault_key"]

    # ── UI Construction ───────────────────────────────────────────────────────
    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG3, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Encryption System", font=F_TITLE, fg=TEXT, bg=BG3).pack()
        tk.Label(hdr, text="Fernet · AES-128-CBC + HMAC-SHA256", font=F_SMALL, fg=MUTED, bg=BG3).pack()

        # Tab bar
        bar = tk.Frame(self, bg=BG2)
        bar.pack(fill="x")
        self._btn_enc  = self._tab_btn(bar, "🔒  Encrypt",  lambda: self._show("enc"))
        self._btn_dec  = self._tab_btn(bar, "🔓  Decrypt",  lambda: self._show("dec"))
        self._btn_keys = self._tab_btn(bar, "🗝️  My Keys",  lambda: self._show("keys"))
        self._btn_enc.pack(side="left", fill="x", expand=True)
        self._btn_dec.pack(side="left", fill="x", expand=True)
        self._btn_keys.pack(side="left", fill="x", expand=True)

        # Panels
        self._panes: dict[str, tk.Frame] = {}

        enc = tk.Frame(self, bg=BG)
        self._panes["enc"] = enc
        self._build_encrypt_pane(enc)

        dec = tk.Frame(self, bg=BG)
        self._panes["dec"] = dec
        self._build_decrypt_pane(dec)

        keys = tk.Frame(self, bg=BG)
        self._panes["keys"] = keys
        self._build_keys_pane(keys)

        self._show("enc")

        # Footer
        ftr = tk.Frame(self, bg=BG3, pady=8)
        ftr.pack(side="bottom", fill="x")
        tk.Label(ftr, text="Made With ❤️ by Lux_", font=F_SMALL, fg=MUTED, bg=BG3).pack(side="left", padx=10)
        self._update_btn = tk.Button(
            ftr,
            text="Verifier les MAJ",
            font=F_SMALL,
            fg=MUTED,
            bg=BG3,
            activeforeground=TEXT,
            activebackground=BG2,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._check_updates_manual,
        )
        self._update_btn.pack(side="right", padx=10)

    def _tab_btn(self, parent, text: str, cmd) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 11),
            fg=TEXT,
            bg=BG2,
            activeforeground=TEXT,
            activebackground=BG3,
            relief="flat",
            bd=0,
            pady=10,
            cursor="hand2",
            command=cmd,
        )

    def _on_resize(self, event):
        if event.widget is self:
            wl = max(300, event.width - 60)
            self._enc_status.config(wraplength=wl)
            self._dec_status.config(wraplength=wl)

    def _show(self, tab: str):
        for pane in self._panes.values():
            pane.pack_forget()
        self._panes[tab].pack(fill="both", expand=True, padx=24, pady=20)
        self._btn_enc.config( bg=ACCENT if tab == "enc"  else BG2, fg=TEXT if tab == "enc"  else MUTED)
        self._btn_dec.config( bg=ACCENT if tab == "dec"  else BG2, fg=TEXT if tab == "dec"  else MUTED)
        self._btn_keys.config(bg=ACCENT if tab == "keys" else BG2, fg=TEXT if tab == "keys" else MUTED)
        if tab == "keys":
            self._refresh_keys()

    # ── Encryption Tab ────────────────────────────────────────────────────────

    def _build_encrypt_pane(self, parent: tk.Frame):
        tk.Label(parent, text="Select a folder to encrypt",
                 font=F_BODY, fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 8))

        self._enc_drop = DropZone(parent, height=150)
        self._enc_drop.pack(fill="x", pady=(0, 4))
        ghost_btn(parent, "📂  Or browse a folder", self._enc_drop.browse_folder).pack(
            anchor="w", pady=(0, 12)
        )

        # Algorithm selector
        tk.Label(parent, text="Algorithm", font=("Segoe UI", 10, "bold"),
                 fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 6))

        self._algo_var = tk.StringVar(value=ALGO_FERNET)
        algo_row = tk.Frame(parent, bg=BG)
        algo_row.pack(anchor="w", pady=(0, 16))

        for algo_id, label in ALGO_LABELS.items():
            tk.Radiobutton(
                algo_row,
                text=label,
                variable=self._algo_var,
                value=algo_id,
                font=F_SMALL,
                fg=TEXT,
                bg=BG,
                activeforeground=TEXT,
                activebackground=BG,
                selectcolor=BG3,
                cursor="hand2",
            ).pack(side="left", padx=(0, 20))

        self._enc_go = action_btn(parent, "🔒  Encrypt", self._do_encrypt)
        self._enc_go.pack(fill="x", pady=(0, 16))

        # Result zone (hidden initially)
        self._enc_result = tk.Frame(parent, bg=BG)

        tk.Label(self._enc_result, text="Decryption key",
                 font=("Segoe UI", 10, "bold"), fg=MUTED, bg=BG).pack(anchor="w")

        key_row = tk.Frame(self._enc_result, bg=BG)
        key_row.pack(fill="x", pady=(4, 0))

        self._enc_key = tk.StringVar()
        tk.Entry(
            key_row,
            textvariable=self._enc_key,
            font=F_MONO,
            fg=SUCCESS,
            bg=BG3,
            readonlybackground=BG3,
            insertbackground=TEXT,
            relief="flat",
            state="readonly",
        ).pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))

        tk.Button(
            key_row,
            text="📋 Copy",
            font=F_SMALL,
            fg=TEXT,
            bg=BG3,
            activeforeground=TEXT,
            activebackground=ACCENT,
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
            command=self._copy_key,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            key_row,
            text="💾 Save",
            font=F_SMALL,
            fg=TEXT,
            bg=SUCCESS,
            activeforeground=TEXT,
            activebackground="#00a381",
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
            command=self._open_save_popup,
        ).pack(side="left")

        self._enc_status = tk.Label(
            self._enc_result,
            text="",
            font=F_SMALL,
            fg=SUCCESS,
            bg=BG,
            wraplength=600,
            justify="left",
        )
        self._enc_status.pack(anchor="w", pady=(10, 0))

        ghost_btn(self._enc_result, "↩  Encrypt another file or folder", self._reset_encrypt).pack(
            anchor="w", pady=(10, 0)
        )

    def _do_encrypt(self):
        path = self._enc_drop.selected_path
        if not path:
            messagebox.showwarning("Warning", "Please first select a file or folder.")
            return
        self._enc_go.config(state="disabled", text="Encrypting…")

        algo    = self._algo_var.get()
        is_file = self._enc_drop.is_file

        def worker():
            try:
                if is_file:
                    out, key = encrypt_file(path, algo)
                    self.after(0, lambda: self._enc_done(out, key, 1, is_file=True))
                else:
                    out, key, count = encrypt_folder(path, algo)
                    self.after(0, lambda: self._enc_done(out, key, count, is_file=False))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self._enc_err(err))
        threading.Thread(target=worker, daemon=True).start()

    def _enc_done(self, out: str, key: str, count: int, *, is_file: bool = False):
        self._enc_go.config(state="normal", text="🔒  Encrypt")
        self._enc_key.set(key)
        icon = "📄" if is_file else "📁"
        self._enc_status.config(
            text=f"✅  {count} file(s) encrypted\n{icon}  {out}",
            fg=SUCCESS,
        )
        self._enc_result.pack(fill="x")

    def _enc_err(self, msg: str):
        self._enc_go.config(state="normal", text="🔒  Encrypt")
        messagebox.showerror("Error", msg)

    def _copy_key(self):
        key = self._enc_key.get()
        if key:
            self.clipboard_clear()
            self.clipboard_append(key)
            messagebox.showinfo(
                "Key copied",
                "Key copied to clipboard!\n\n"
                "⚠️  Keep it safe — without it,\n"
                "the encrypted folder will be unrecoverable."
            )

    def _open_save_popup(self):
        key = self._enc_key.get()
        if not key:
            return
        folder = self._enc_drop.selected_path or ""

        popup = tk.Toplevel(self, bg=BG)
        popup.title("Save key")
        popup.geometry("380x190")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="Key name", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=BG).pack(pady=(20, 6))

        name_var = tk.StringVar(value=os.path.basename(folder))
        entry = tk.Entry(popup, textvariable=name_var, font=F_BODY, fg=TEXT, bg=BG3,
                         insertbackground=TEXT, relief="flat")
        entry.pack(fill="x", padx=24, ipady=8)
        entry.select_range(0, "end")
        entry.focus_set()

        msg = tk.Label(popup, text="", font=F_SMALL, fg=ERROR, bg=BG)
        msg.pack(pady=(4, 0))

        def _confirm():
            n = name_var.get().strip()
            if not n:
                msg.config(text="Name cannot be empty.")
                return
            ok = self._km.save_key(n, key, folder, self._algo_var.get())
            if ok:
                popup.destroy()
                messagebox.showinfo("Key saved", f"Key « {n} » saved in My Keys.")
            else:
                msg.config(text=f"« {n} » already exists — choose another name.")

        tk.Button(popup, text="💾 Save", font=("Segoe UI", 11, "bold"),
                  fg=TEXT, bg=SUCCESS, activeforeground=TEXT, activebackground="#00a381",
                  relief="flat", bd=0, pady=10, cursor="hand2",
                  command=_confirm).pack(fill="x", padx=24, pady=(8, 0))

        entry.bind("<Return>", lambda _: _confirm())

    def _reset_encrypt(self):
        self._enc_drop.reset()
        self._enc_key.set("")
        self._enc_status.config(text="")
        self._enc_result.pack_forget()

    # ── Decryption Tab ────────────────────────────────────────────────────────

    def _build_decrypt_pane(self, parent: tk.Frame):
        tk.Label(parent, text="Select an encrypted file or folder",
                 font=F_BODY, fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 8))

        self._dec_drop = DropZone(parent, height=130)
        self._dec_drop.pack(fill="x", pady=(0, 4))
        ghost_btn(parent, "📂  Or browse a folder", self._dec_drop.browse_folder).pack(
            anchor="w", pady=(0, 12)
        )

        key_hdr = tk.Frame(parent, bg=BG)
        key_hdr.pack(fill="x", pady=(0, 4))
        tk.Label(key_hdr, text="Decryption key",
                 font=("Segoe UI", 10, "bold"), fg=MUTED, bg=BG).pack(side="left")
        tk.Button(
            key_hdr,
            text="🗝️ Choose from my keys",
            font=F_SMALL,
            fg=ACCENT,
            bg=BG,
            activeforeground=TEXT,
            activebackground=BG2,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._pick_saved_key,
        ).pack(side="right")

        self._dec_key = tk.StringVar()
        tk.Entry(
            parent,
            textvariable=self._dec_key,
            font=F_MONO,
            fg=TEXT,
            bg=BG3,
            insertbackground=TEXT,
            relief="flat",
        ).pack(fill="x", ipady=8, pady=(0, 16))

        self._dec_go = action_btn(parent, "🔓  Decrypt", self._do_decrypt)
        self._dec_go.pack(fill="x", pady=(0, 16))

        self._dec_status = tk.Label(
            parent,
            text="",
            font=F_SMALL,
            fg=SUCCESS,
            bg=BG,
            wraplength=600,
            justify="left",
        )
        self._dec_status.pack(anchor="w")

        if not DND_AVAILABLE:
            tk.Label(
                parent,
                text="ℹ️  Install tkinterdnd2 to enable drag and drop.",
                font=F_SMALL,
                fg=MUTED,
                bg=BG,
            ).pack(anchor="w", pady=(12, 0))

    def _pick_saved_key(self):
        keys = self._km.all_keys()
        if not keys:
            messagebox.showinfo("My Keys", "No saved keys.\nFirst encrypt a folder and save its key.")
            return

        popup = tk.Toplevel(self, bg=BG)
        popup.title("Choose a key")
        popup.geometry("500x360")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="Select a saved key",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=BG).pack(pady=(16, 8))

        frame = tk.Frame(popup, bg=BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        selected = tk.StringVar(value="")

        for k in keys:
            row = tk.Frame(inner, bg=BG2, pady=8, padx=10)
            row.pack(fill="x", pady=3)

            def _choose(key_val=k["key"]):
                selected.set(key_val)
                popup.destroy()

            tk.Label(row, text=k["name"], font=("Segoe UI", 10, "bold"), fg=TEXT, bg=BG2,
                     anchor="w").grid(row=0, column=0, sticky="w")
            algo_label = ALGO_LABELS.get(k.get("algo", ALGO_FERNET), "Fernet  (AES-128-CBC)")
            folder_short = k["folder"][-40:] if len(k["folder"]) > 40 else k["folder"]
            tk.Label(row, text=f"🔑 {algo_label}  ·  📁 {folder_short}", font=F_SMALL, fg=MUTED, bg=BG2,
                     anchor="w").grid(row=1, column=0, sticky="w")
            tk.Label(row, text=k["date"], font=F_SMALL, fg=MUTED, bg=BG2,
                     anchor="e").grid(row=0, column=1, sticky="e", padx=(12, 0))
            tk.Button(row, text="Use", font=F_SMALL, fg=TEXT, bg=ACCENT,
                      activeforeground=TEXT, activebackground="#c0392b",
                      relief="flat", bd=0, padx=8, pady=4, cursor="hand2",
                      command=_choose).grid(row=1, column=1, sticky="e", padx=(12, 0))
            row.columnconfigure(0, weight=1)

        popup.wait_window()
        if selected.get():
            self._dec_key.set(selected.get())

    def _do_decrypt(self):
        path = self._dec_drop.selected_path
        key  = self._dec_key.get().strip()
        if not path:
            messagebox.showwarning("Warning", "Please first select an encrypted file or folder.")
            return
        if not key:
            messagebox.showwarning("Warning", "Please enter the decryption key.")
            return

        self._dec_go.config(state="disabled", text="Decrypting…")

        is_file = self._dec_drop.is_file

        def worker():
            try:
                if is_file:
                    out = decrypt_file(path, key)
                    self.after(0, lambda: self._dec_done(out, 1, is_file=True))
                else:
                    out, count = decrypt_folder(path, key)
                    self.after(0, lambda: self._dec_done(out, count, is_file=False))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self._dec_err(err))
        threading.Thread(target=worker, daemon=True).start()

    def _dec_done(self, out: str, count: int, *, is_file: bool = False):
        self._dec_go.config(state="normal", text="🔓  Decrypt")
        icon = "📄" if is_file else "📁"
        self._dec_status.config(
            text=f"✅  {count} file(s) decrypted\n{icon}  {out}",
            fg=SUCCESS,
        )

    def _dec_err(self, msg: str):
        self._dec_go.config(state="normal", text="🔓  Decrypt")
        self._dec_status.config(text=f"❌  {msg}", fg=ERROR)

    # ── Key Management Tab ────────────────────────────────────────────────────

    def _build_keys_pane(self, parent: tk.Frame):
        hdr = tk.Frame(parent, bg=BG)
        hdr.pack(fill="x", pady=(0, 12))
        tk.Label(hdr, text="Saved keys", font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=BG).pack(side="left")
        tk.Button(hdr, text="⟳ Refresh", font=F_SMALL, fg=MUTED, bg=BG,
                  activeforeground=TEXT, activebackground=BG2, relief="flat", bd=0,
                  cursor="hand2", command=self._refresh_keys).pack(side="right")

        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill="both", expand=True)

        self._keys_canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(wrap, orient="vertical", command=self._keys_canvas.yview)
        self._keys_inner = tk.Frame(self._keys_canvas, bg=BG)

        self._keys_inner.bind(
            "<Configure>",
            lambda e: self._keys_canvas.configure(scrollregion=self._keys_canvas.bbox("all"))
        )
        self._keys_canvas.create_window((0, 0), window=self._keys_inner, anchor="nw")
        self._keys_canvas.configure(yscrollcommand=sb.set)
        self._keys_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._keys_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._empty_label = tk.Label(
            self._keys_inner,
            text="No saved keys.\nEncrypt a folder and save its key.",
            font=F_BODY, fg=MUTED, bg=BG, justify="center",
        )

    def _on_mousewheel(self, event):
        self._keys_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _refresh_keys(self):
        for w in self._keys_inner.winfo_children():
            w.destroy()

        keys = self._km.all_keys()
        if not keys:
            self._empty_label = tk.Label(
                self._keys_inner,
                text="No saved keys.\nEncrypt a folder and save its key.",
                font=F_BODY,
                fg=MUTED,
                bg=BG,
                justify="center",
            )
            self._empty_label.pack(expand=True)
            return

        for k in keys:
            self._key_card(self._keys_inner, k)

    def _key_card(self, parent: tk.Frame, k: dict):
        card = tk.Frame(parent, bg=BG2, padx=14, pady=10)
        card.pack(fill="x", pady=4)

        top = tk.Frame(card, bg=BG2)
        top.pack(fill="x")
        tk.Label(top, text=k["name"], font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG2,
                 anchor="w").pack(side="left")
        tk.Label(top, text=k["date"], font=F_SMALL, fg=MUTED, bg=BG2,
                 anchor="e").pack(side="right")

        algo_label = ALGO_LABELS.get(k.get("algo", ALGO_FERNET), "Fernet  (AES-128-CBC)")
        tk.Label(card, text=f"🔑 {algo_label}", font=F_SMALL, fg=ACCENT, bg=BG2,
                 anchor="w").pack(fill="x", pady=(2, 0))
        folder_short = k["folder"][-55:] if len(k["folder"]) > 55 else k["folder"]
        tk.Label(card, text=f"📁 {folder_short}", font=F_SMALL, fg=MUTED, bg=BG2,
                 anchor="w").pack(fill="x", pady=(0, 6))

        bottom = tk.Frame(card, bg=BG2)
        bottom.pack(fill="x")

        key_var = tk.StringVar(value="•" * 44)
        key_entry = tk.Entry(
            bottom,
            textvariable=key_var,
            font=F_MONO,
            fg=MUTED,
            bg=BG3,
            readonlybackground=BG3,
            relief="flat",
            state="readonly",
            width=32,
        )
        key_entry.pack(side="left", ipady=5, padx=(0, 6))

        visible = [False]

        def _toggle(kv=k["key"]):
            if not visible[0]:
                key_var.set(kv)
                visible[0] = True
            else:
                key_var.set("•" * 44)
                visible[0] = False

        tk.Button(bottom, text="👁", font=F_SMALL, fg=MUTED, bg=BG3,
                  activeforeground=TEXT, activebackground=BG2,
                  relief="flat", bd=0, padx=6, pady=5, cursor="hand2",
                  command=_toggle).pack(side="left", padx=(0, 4))

        tk.Button(bottom, text="📋 Copy", font=F_SMALL, fg=TEXT, bg=BG3,
                  activeforeground=TEXT, activebackground=ACCENT,
                  relief="flat", bd=0, padx=8, pady=5, cursor="hand2",
                  command=lambda kv=k["key"]: self._copy_saved(kv)).pack(side="left", padx=(0, 4))

        tk.Button(bottom, text="🔓 Use", font=F_SMALL, fg=TEXT, bg=BG3,
                  activeforeground=TEXT, activebackground=SUCCESS,
                  relief="flat", bd=0, padx=8, pady=5, cursor="hand2",
                  command=lambda kv=k["key"]: self._use_key(kv)).pack(side="left", padx=(0, 4))

        tk.Button(bottom, text="✏️ Rename", font=F_SMALL, fg=MUTED, bg=BG2,
                  activeforeground=TEXT, activebackground=BG3,
                  relief="flat", bd=0, padx=6, pady=5, cursor="hand2",
                  command=lambda name=k["name"]: self._rename_key(name)).pack(side="right", padx=(4, 0))

        tk.Button(bottom, text="🗑 Delete", font=F_SMALL, fg=ERROR, bg=BG2,
                  activeforeground=TEXT, activebackground="#5a1a1a",
                  relief="flat", bd=0, padx=6, pady=5, cursor="hand2",
                  command=lambda name=k["name"]: self._delete_key(name)).pack(side="right", padx=(4, 0))

    def _copy_saved(self, key: str):
        self.clipboard_clear()
        self.clipboard_append(key)
        messagebox.showinfo("Key copied", "Key copied to clipboard.")

    def _use_key(self, key: str):
        self._dec_key.set(key)
        self._show("dec")

    def _delete_key(self, name: str):
        if messagebox.askyesno("Delete", f"Delete key « {name} »?\n\nThis action is irreversible."):
            self._km.delete_key(name)
            self._refresh_keys()

    def _rename_key(self, old_name: str):
        popup = tk.Toplevel(self, bg=BG)
        popup.title("Rename key")
        popup.geometry("340x150")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="New name", font=F_BODY, fg=TEXT, bg=BG).pack(pady=(20, 6))

        new_name = tk.StringVar(value=old_name)
        entry = tk.Entry(popup, textvariable=new_name, font=F_BODY, fg=TEXT, bg=BG3,
                         insertbackground=TEXT, relief="flat")
        entry.pack(fill="x", padx=24, ipady=8)
        entry.select_range(0, "end")
        entry.focus_set()

        msg = tk.Label(popup, text="", font=F_SMALL, fg=ERROR, bg=BG)
        msg.pack(pady=(4, 0))

        def _confirm():
            n = new_name.get().strip()
            if not n:
                msg.config(text="Name cannot be empty.")
                return
            ok = self._km.rename_key(old_name, n)
            if ok:
                popup.destroy()
                self._refresh_keys()
            else:
                msg.config(text=f"« {n} » already exists.")

        tk.Button(popup, text="Confirm", font=F_BODY, fg=TEXT, bg=ACCENT,
                  activeforeground=TEXT, activebackground="#c0392b",
                  relief="flat", bd=0, pady=8, cursor="hand2",
                  command=_confirm).pack(fill="x", padx=24, pady=(8, 0))

        entry.bind("<Return>", lambda _: _confirm())

    # ── Updates ───────────────────────────────────────────────────────────────

    def _check_updates_manual(self):
        self._start_update_check(silent=False)

    def _check_updates_silent(self):
        self._start_update_check(silent=True)

    def _start_update_check(self, *, silent: bool):
        if self._is_checking_update:
            return

        self._is_checking_update = True
        if hasattr(self, "_update_btn"):
            self._update_btn.config(state="disabled", text="Verification...")

        def worker():
            result = self._updater.check_for_updates()
            self.after(0, lambda: self._on_update_check_done(result, silent=silent))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_check_done(self, result, *, silent: bool):
        self._is_checking_update = False
        if hasattr(self, "_update_btn"):
            self._update_btn.config(state="normal", text="Verifier les MAJ")

        if result.error:
            if not silent:
                messagebox.showerror("Mise a jour", result.error)
            return

        if not result.update_available:
            if not silent:
                messagebox.showinfo("Mise a jour", result.message)
            return

        asset = result.asset
        if asset is None:
            if not silent:
                messagebox.showinfo("Mise a jour", result.message)
            return

        notes = (result.release_notes or "").strip()
        if len(notes) > 350:
            notes = notes[:350].rstrip() + "..."

        prompt = (
            f"Une nouvelle version est disponible: {result.latest_version}\n\n"
            f"Fichier compatible detecte: {asset.name}\n"
            f"Taille: {asset.size // 1024} Ko\n"
        )
        if notes:
            prompt += f"\nNotes:\n{notes}\n"
        prompt += "\nVoulez-vous telecharger cette mise a jour maintenant ?"

        if messagebox.askyesno("Mise a jour disponible", prompt):
            self._download_update_asset(asset, result.latest_version or "")

    def _download_update_asset(self, asset, version_label: str):
        if hasattr(self, "_update_btn"):
            self._update_btn.config(state="disabled", text="Telechargement...")

        def worker():
            try:
                downloaded = self._updater.download_asset(asset)
                self.after(0, lambda: self._on_update_download_done(downloaded, version_label))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Mise a jour", f"Echec du telechargement: {exc}"))
            finally:
                self.after(0, self._reset_update_button)

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_download_done(self, downloaded_path: Path, version_label: str):
        msg = (
            f"Version {version_label} telechargee.\n\n"
            f"Fichier: {downloaded_path}\n\n"
            "Ouvrir le fichier maintenant ?"
        )
        if messagebox.askyesno("Mise a jour telechargee", msg):
            self._open_downloaded_file(downloaded_path)

    def _reset_update_button(self):
        if hasattr(self, "_update_btn"):
            self._update_btn.config(state="normal", text="Verifier les MAJ")

    def _open_downloaded_file(self, path: Path):
        try:
            if os.name == "nt":
                os.startfile(str(path))
                return
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
                return
            subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Mise a jour", f"Impossible d'ouvrir le fichier: {exc}")


if __name__ == "__main__":
    import traceback
    from pathlib import Path
    log_path = Path.home() / "enc_debug.log"
    try:
        App().mainloop()
    except Exception:
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        raise
