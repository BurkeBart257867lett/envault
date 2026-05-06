"""Tests for envault crypto and vault modules."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from envault.crypto import encrypt, decrypt, encode_token, decode_token


# ---------------------------------------------------------------------------
# crypto tests
# ---------------------------------------------------------------------------

class TestCrypto:
    def test_encrypt_returns_bytes(self):
        result = encrypt("hello", "password")
        assert isinstance(result, bytes)

    def test_roundtrip(self):
        plaintext = "DATABASE_URL=postgres://localhost/mydb"
        password = "s3cr3t!"
        token = encrypt(plaintext, password)
        assert decrypt(token, password) == plaintext

    def test_wrong_password_raises(self):
        token = encrypt("secret", "correct")
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(token, "wrong")

    def test_corrupted_token_raises(self):
        token = encrypt("secret", "pass")
        corrupted = token[:-4] + b"\x00\x00\x00\x00"
        with pytest.raises(ValueError):
            decrypt(corrupted, "pass")

    def test_short_token_raises(self):
        with pytest.raises(ValueError, match="too short"):
            decrypt(b"short", "pass")

    def test_encode_decode_token(self):
        token = encrypt("data", "pw")
        encoded = encode_token(token)
        assert isinstance(encoded, str)
        assert decode_token(encoded) == token

    def test_different_salts_each_call(self):
        t1 = encrypt("same", "same")
        t2 = encrypt("same", "same")
        assert t1 != t2  # different salt/nonce each time


# ---------------------------------------------------------------------------
# vault tests (using tmp directory)
# ---------------------------------------------------------------------------

class TestVault:
    @pytest.fixture(autouse=True)
    def _patch_vault_dir(self, tmp_path):
        import envault.vault as vault_mod
        original = vault_mod.VAULT_DIR
        vault_mod.VAULT_DIR = tmp_path / "vaults"
        yield
        vault_mod.VAULT_DIR = original

    def test_store_and_load(self):
        from envault.vault import store_secret, load_secret
        store_secret("myapp", "production", "KEY=value", "masterpass")
        result = load_secret("myapp", "production", "masterpass")
        assert result == "KEY=value"

    def test_load_missing_raises(self):
        from envault.vault import load_secret
        with pytest.raises(FileNotFoundError):
            load_secret("ghost", "nope", "pass")

    def test_list_secrets(self):
        from envault.vault import store_secret, list_secrets
        store_secret("proj", "dev", "A=1", "pw")
        store_secret("proj", "prod", "B=2", "pw")
        secrets = list_secrets("proj")
        assert set(secrets) == {"dev", "prod"}

    def test_delete_secret(self):
        from envault.vault import store_secret, delete_secret, list_secrets
        store_secret("proj", "staging", "C=3", "pw")
        assert delete_secret("proj", "staging") is True
        assert "staging" not in list_secrets("proj")

    def test_delete_nonexistent_returns_false(self):
        from envault.vault import delete_secret
        assert delete_secret("proj", "ghost") is False

    def test_list_projects(self):
        from envault.vault import store_secret, list_projects
        store_secret("alpha", "env", "X=1", "pw")
        store_secret("beta", "env", "Y=2", "pw")
        projects = list_projects()
        assert "alpha" in projects
        assert "beta" in projects
