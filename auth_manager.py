import hashlib
import hmac
import json
import secrets
from pathlib import Path


AUTH_FILE = Path.home() / ".enc_auth.json"


class AuthManager:
    """Gestion du mot de passe d'acces (hash PBKDF2 + sel)."""

    def __init__(self, path: Path = AUTH_FILE, iterations: int = 310000):
        self._path = path
        self._iterations = iterations

    def is_configured(self) -> bool:
        if not self._path.exists():
            return False
        data = self._load()
        return bool(data.get("salt") and data.get("password_hash"))

    def setup_password(self, password: str) -> None:
        salt = secrets.token_bytes(16)
        password_hash = self._hash_password(password, salt)
        payload = {
            "salt": salt.hex(),
            "password_hash": password_hash.hex(),
            "iterations": self._iterations,
            "algo": "pbkdf2_sha256",
        }
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def verify_password(self, password: str) -> bool:
        data = self._load()
        if not data:
            return False

        salt_hex = data.get("salt")
        expected_hex = data.get("password_hash")
        iterations = int(data.get("iterations", self._iterations))

        if not salt_hex or not expected_hex:
            return False

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(candidate, expected)

    def _hash_password(self, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self._iterations,
        )

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return {}
