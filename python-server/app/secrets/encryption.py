"""AES-256-GCM encryption for secrets."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _load_master_key(key_str: str = "", key_file: str = "") -> bytes:
    """Load or generate a 32-byte master key."""
    if key_str:
        raw = key_str.encode()
        if len(raw) == 64:  # hex-encoded
            return bytes.fromhex(key_str)
        return base64.b64decode(raw)

    if key_file:
        path = Path(key_file)
        if path.exists():
            data = path.read_bytes().strip()
            if len(data) == 64:
                return bytes.fromhex(data.decode())
            return base64.b64decode(data)

    # Default: generate and persist to ~/.paperclip/master.key
    default_path = Path.home() / ".paperclip" / "master.key"
    if default_path.exists():
        return bytes.fromhex(default_path.read_text().strip())

    key = os.urandom(32)
    default_path.parent.mkdir(parents=True, exist_ok=True)
    default_path.write_text(key.hex())
    default_path.chmod(0o600)
    return key


class LocalEncryptedProvider:
    """AES-256-GCM secret encryption."""

    def __init__(self, master_key: str = "", master_key_file: str = "") -> None:
        self._key = _load_master_key(master_key, master_key_file)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> dict:
        """Encrypt plaintext → {nonce, ciphertext} both base64-encoded."""
        nonce = os.urandom(12)
        ct = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        return {
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ct).decode(),
        }

    def decrypt(self, material: dict) -> str:
        """Decrypt material dict → plaintext string."""
        nonce = base64.b64decode(material["nonce"])
        ct = base64.b64decode(material["ciphertext"])
        return self._aesgcm.decrypt(nonce, ct, None).decode()

    def value_sha256(self, plaintext: str) -> str:
        return hashlib.sha256(plaintext.encode()).hexdigest()
