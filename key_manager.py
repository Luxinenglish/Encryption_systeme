import json
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet

KEYS_FILE = Path.home() / ".enc_keys.json"


class KeyManager:
    """Stockage persistant des cles, chiffre avec la cle de coffre."""

    def __init__(self, path: Path = KEYS_FILE, vault_key: bytes | None = None):
        self._path = path
        self._fernet = Fernet(vault_key) if vault_key else None

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []

        raw = self._path.read_bytes()
        if not raw:
            return []

        # Si pas de chiffrement configure, fallback legacy plaintext
        if not self._fernet:
            try:
                data = json.loads(raw.decode("utf-8"))
                return data if isinstance(data, list) else []
            except Exception:
                return []

        # Format chiffre attendu: {"v":1,"enc":"fernet","data":"<token>"}
        try:
            payload = json.loads(raw.decode("utf-8"))
            if isinstance(payload, dict) and payload.get("enc") == "fernet":
                token = payload.get("data", "").encode("utf-8")
                plain = self._fernet.decrypt(token)
                data = json.loads(plain.decode("utf-8"))
                return data if isinstance(data, list) else []
        except Exception:
            pass

        # Migration auto: ancien fichier en clair => rechiffrer
        try:
            legacy = json.loads(raw.decode("utf-8"))
            if isinstance(legacy, list):
                self._save(legacy)
                return legacy
        except Exception:
            pass

        return []

    def _save(self, keys: list[dict]):
        plain = json.dumps(keys, ensure_ascii=False, indent=2).encode("utf-8")

        if not self._fernet:
            self._path.write_text(plain.decode("utf-8"), encoding="utf-8")
            return

        token = self._fernet.encrypt(plain).decode("utf-8")
        payload = {
            "v": 1,
            "enc": "fernet",
            "data": token,
        }
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def all_keys(self) -> list[dict]:
        return self._load()

    def save_key(self, name: str, key: str, folder: str, algo: str = "fernet") -> bool:
        keys = self._load()
        if any(k["name"] == name for k in keys):
            return False
        keys.insert(0, {
            "name": name,
            "key": key,
            "folder": folder,
            "algo": algo,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self._save(keys)
        return True

    def delete_key(self, name: str):
        keys = [k for k in self._load() if k["name"] != name]
        self._save(keys)

    def rename_key(self, old_name: str, new_name: str) -> bool:
        keys = self._load()
        if any(k["name"] == new_name for k in keys):
            return False
        for k in keys:
            if k["name"] == old_name:
                k["name"] = new_name
                break
        self._save(keys)
        return True