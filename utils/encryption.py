"""
Encryption Manager - Handles password encryption/decryption for stored connections.

This module provides encryption functionality using Fernet symmetric encryption
with password-based key derivation (PBKDF2HMAC).
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data like database passwords.

    Uses Fernet symmetric encryption with a key derived from a fixed password
    and salt. This provides basic encryption for stored connection configurations.
    """

    def __init__(self, password: bytes = b"mysql_client_default_password_2023",
                 salt: bytes = b"mysql_salt_2023"):
        """
        Initialize the encryption manager and generate the encryption key.

        Args:
            password: Password bytes for key derivation
            salt: Salt bytes for key derivation
        """
        self._key = self._generate_key(password, salt)

    def _generate_key(self, password: bytes, salt: bytes) -> bytes:
        """
        Generate an encryption key using PBKDF2HMAC key derivation.

        Args:
            password: Password bytes
            salt: Salt bytes

        Returns:
            Base64-encoded key suitable for Fernet
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The plaintext string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        fernet = Fernet(self._key)
        encrypted = fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_text: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string, empty string if decryption fails
        """
        if not encrypted_text:
            return ""

        try:
            fernet = Fernet(self._key)
            encrypted_bytes = base64.b64decode(encrypted_text.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            # Return empty string on any decryption failure
            return ""
