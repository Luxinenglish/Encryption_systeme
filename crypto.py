import base64
import os
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

# ─── Algorithm registry ────────────────────────────────────────────────────────

ALGO_FERNET   = "fernet"
ALGO_AES256   = "aes256gcm"
ALGO_CHACHA20 = "chacha20"

ALGO_LABELS = {
    ALGO_FERNET:   "Fernet  (AES-128-CBC)",
    ALGO_AES256:   "AES-256-GCM",
    ALGO_CHACHA20: "ChaCha20-Poly1305",
}

# Magic header written at the start of non-Fernet encrypted files.
# Fernet tokens always start with 0x80, so there is no collision.
_MAGIC      = b"\xEE\xCC"
_ALGO_BYTE  = {ALGO_AES256: b"\x01", ALGO_CHACHA20: b"\x02"}
_BYTE_ALGO  = {v: k for k, v in _ALGO_BYTE.items()}
_NONCE_LEN  = 12


# ─── Key generation ────────────────────────────────────────────────────────────

def generate_key(algo: str) -> str:
    if algo == ALGO_FERNET:
        return Fernet.generate_key().decode()
    return base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")


# ─── Low-level encrypt / decrypt ───────────────────────────────────────────────

def _raw_encrypt(data: bytes, key_str: str, algo: str) -> bytes:
    if algo == ALGO_FERNET:
        return Fernet(key_str.encode()).encrypt(data)

    # Pad key to correct base64 length before decoding
    key = base64.urlsafe_b64decode(key_str + "==")
    nonce = os.urandom(_NONCE_LEN)

    if algo == ALGO_AES256:
        ct = AESGCM(key).encrypt(nonce, data, None)
    else:  # ALGO_CHACHA20
        ct = ChaCha20Poly1305(key).encrypt(nonce, data, None)

    return _MAGIC + _ALGO_BYTE[algo] + nonce + ct


def _raw_decrypt(data: bytes, key_str: str) -> bytes:
    if data[:2] != _MAGIC:
        # Fernet (no magic header)
        return Fernet(key_str.strip().encode()).decrypt(data)

    algo = _BYTE_ALGO.get(data[2:3])
    if algo is None:
        raise ValueError("Unknown encryption algorithm in file header.")

    key   = base64.urlsafe_b64decode(key_str.strip() + "==")
    nonce = data[3: 3 + _NONCE_LEN]
    ct    = data[3 + _NONCE_LEN:]

    if algo == ALGO_AES256:
        return AESGCM(key).decrypt(nonce, ct, None)
    else:
        return ChaCha20Poly1305(key).decrypt(nonce, ct, None)


# ─── Folder operations ─────────────────────────────────────────────────────────

def encrypt_folder(folder_path: str, algo: str = ALGO_FERNET) -> tuple[str, str, int]:
    """
    Encrypts all files in a folder with the chosen algorithm.
    Returns (output_path, key, file_count).
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError(f"Folder not found: {folder_path}")

    key = generate_key(algo)
    out_folder = folder.parent / (folder.name + "_encrypted")
    out_folder.mkdir(exist_ok=True)

    count = 0
    for src in folder.rglob("*"):
        if src.is_file():
            rel = src.relative_to(folder)
            dst = out_folder / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(_raw_encrypt(src.read_bytes(), key, algo))
            count += 1

    return str(out_folder), key, count


def encrypt_file(file_path: str, algo: str = ALGO_FERNET) -> tuple[str, str]:
    """
    Encrypts a single file.
    Returns (output_path, key).
    """
    src = Path(file_path)
    if not src.is_file():
        raise ValueError(f"File not found: {file_path}")

    key = generate_key(algo)
    dst = src.parent / f"{src.stem}_encrypted{src.suffix}"
    dst.write_bytes(_raw_encrypt(src.read_bytes(), key, algo))
    return str(dst), key


def decrypt_file(file_path: str, key_str: str) -> str:
    """
    Decrypts a single file. Algorithm is auto-detected from its header.
    Returns output_path.
    """
    src = Path(file_path)
    if not src.is_file():
        raise ValueError(f"File not found: {file_path}")

    stem = src.stem.removesuffix("_encrypted")
    dst = src.parent / f"{stem}_decrypted{src.suffix}"
    try:
        dst.write_bytes(_raw_decrypt(src.read_bytes(), key_str))
    except Exception:
        raise ValueError(f"Cannot decrypt « {src.name} ».\nIs the key correct?")
    return str(dst)


def decrypt_folder(folder_path: str, key_str: str) -> tuple[str, int]:
    """
    Decrypts all files in a folder.
    The algorithm is auto-detected from each file's header.
    Returns (output_path, file_count).
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError(f"Folder not found: {folder_path}")

    base = folder.name.removesuffix("_encrypted")
    out_folder = folder.parent / (base + "_decrypted")
    out_folder.mkdir(exist_ok=True)

    count = 0
    for src in folder.rglob("*"):
        if src.is_file():
            rel = src.relative_to(folder)
            dst = out_folder / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                dst.write_bytes(_raw_decrypt(src.read_bytes(), key_str))
                count += 1
            except Exception:
                raise ValueError(
                    f"Cannot decrypt « {src.name} ».\n"
                    "Is the key correct?"
                )

    return str(out_folder), count
