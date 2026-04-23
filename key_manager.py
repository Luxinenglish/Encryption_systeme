import json
from datetime import datetime
from pathlib import Path

KEYS_FILE = Path.home() / ".enc_keys.json"


class KeyManager:
    """Persistent storage of Fernet keys in a JSON file."""

    def __init__(self, path: Path = KEYS_FILE):
        self._path = path

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, keys: list[dict]):
        self._path.write_text(json.dumps(keys, ensure_ascii=False, indent=2), encoding="utf-8")

    def all_keys(self) -> list[dict]:
        return self._load()

    def save_key(self, name: str, key: str, folder: str, algo: str = "fernet") -> bool:
        """Save a key. Returns False if the name already exists."""
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
