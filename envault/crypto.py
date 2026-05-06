"""Encryption and decryption utilities for envault using AES-GCM."""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256-bit


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a password using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations=600_000,
        dklen=KEY_SIZE,
    )


def encrypt(plaintext: str, password: str) -> bytes:
    """Encrypt plaintext string with a password.

    Returns salt + nonce + ciphertext as raw bytes.
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return salt + nonce + ciphertext


def decrypt(token: bytes, password: str) -> str:
    """Decrypt token produced by :func:`encrypt`.

    Raises ValueError on authentication failure.
    """
    if len(token) < SALT_SIZE + NONCE_SIZE:
        raise ValueError("Token is too short to be valid.")
    salt = token[:SALT_SIZE]
    nonce = token[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    ciphertext = token[SALT_SIZE + NONCE_SIZE :]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed: invalid password or corrupted data.") from exc
    return plaintext.decode("utf-8")


def encode_token(token: bytes) -> str:
    """Base64-encode a raw token for storage."""
    return base64.urlsafe_b64encode(token).decode("ascii")


def decode_token(encoded: str) -> bytes:
    """Decode a base64-encoded token back to raw bytes."""
    return base64.urlsafe_b64decode(encoded.encode("ascii"))
